import streamlit as st
from database.connection import execute_query
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

def convert_datetime(dt):
    """Convert datetime object to ISO format string"""
    try:
        return dt.isoformat() if dt else None
    except Exception as e:
        logger.error(f"Error converting datetime: {str(e)}")
        return None

def convert_project_dates(project):
    """Convert all datetime fields in a project dict to ISO format strings"""
    try:
        project['created_at'] = convert_datetime(project['created_at'])
        project['updated_at'] = convert_datetime(project.get('updated_at'))
        project['deleted_at'] = convert_datetime(project.get('deleted_at'))
        project['deadline'] = convert_datetime(project.get('deadline'))
        return project
    except Exception as e:
        logger.error(f"Error converting project dates: {str(e)}")
        return project

def delete_project(project_id, permanent=False):
    """Delete project and all its tasks"""
    try:
        # Verify project exists and get its current state
        project = execute_query("""
            SELECT p.*, COUNT(t.id) as task_count 
            FROM projects p 
            LEFT JOIN tasks t ON p.id = t.project_id 
            WHERE p.id = %s 
            GROUP BY p.id
        """, (project_id,))
        
        if not project:
            logger.error(f"Project {project_id} not found in database")
            return False, "Project not found"
            
        project = project[0]
        project_name = project['name']
        
        # Validate project state
        if not permanent and project.get('deleted_at'):
            logger.error(f"Project {project_id} is already in trash")
            return False, "Project is already in trash"
        
        if permanent and not project.get('deleted_at'):
            logger.error(f"Cannot permanently delete active project {project_id}")
            return False, "Cannot permanently delete an active project"
            
        action_type = 'permanently delete' if permanent else 'move to trash'
        logger.info(f"Attempting to {action_type} project {project_id}: {project_name} with {project['task_count']} tasks")
        
        # Start transaction
        execute_query("BEGIN")
        
        try:
            if permanent:
                # Delete task history first
                logger.info(f"Deleting task history for project {project_id}")
                history_result = execute_query("""
                    DELETE FROM task_history 
                    WHERE task_id IN (SELECT id FROM tasks WHERE project_id = %s)
                    RETURNING id
                """, (project_id,))
                logger.info(f"Deleted {len(history_result) if history_result else 0} task history records")
                
                # Delete task dependencies
                logger.info(f"Deleting task dependencies for project {project_id}")
                dep_result = execute_query("""
                    DELETE FROM task_dependencies 
                    WHERE task_id IN (SELECT id FROM tasks WHERE project_id = %s)
                    OR depends_on_id IN (SELECT id FROM tasks WHERE project_id = %s)
                    RETURNING id
                """, (project_id, project_id))
                logger.info(f"Deleted {len(dep_result) if dep_result else 0} task dependencies")
                
                # Delete subtasks
                logger.info(f"Deleting subtasks for project {project_id}")
                subtask_result = execute_query("""
                    DELETE FROM subtasks 
                    WHERE parent_task_id IN (SELECT id FROM tasks WHERE project_id = %s)
                    RETURNING id
                """, (project_id,))
                logger.info(f"Deleted {len(subtask_result) if subtask_result else 0} subtasks")
                
                # Delete all tasks
                logger.info(f"Deleting tasks for project {project_id}")
                task_result = execute_query("""
                    DELETE FROM tasks 
                    WHERE project_id = %s
                    RETURNING id
                """, (project_id,))
                logger.info(f"Deleted {len(task_result) if task_result else 0} tasks")
                
                # Finally delete the project
                logger.info(f"Permanently deleting project {project_id}")
                result = execute_query("""
                    DELETE FROM projects 
                    WHERE id = %s 
                    RETURNING id, name
                """, (project_id,))
            else:
                # Soft delete project and its tasks
                logger.info(f"Soft deleting project {project_id}")
                result = execute_query("""
                    UPDATE projects 
                    SET deleted_at = CURRENT_TIMESTAMP 
                    WHERE id = %s AND deleted_at IS NULL
                    RETURNING id, name
                """, (project_id,))
                
                if result:
                    # Soft delete all associated tasks
                    logger.info(f"Soft deleting tasks for project {project_id}")
                    task_result = execute_query("""
                        UPDATE tasks 
                        SET deleted_at = CURRENT_TIMESTAMP 
                        WHERE project_id = %s AND deleted_at IS NULL
                        RETURNING id
                    """, (project_id,))
                    logger.info(f"Soft deleted {len(task_result) if task_result else 0} tasks")
            
            if result:
                execute_query("COMMIT")
                # Clear cache after successful deletion
                if 'query_cache' in st.session_state:
                    st.session_state.query_cache.clear()
                action = 'permanently deleted' if permanent else 'moved to trash'
                success_msg = f"Project '{project_name}' successfully {action}"
                logger.info(success_msg)
                return True, success_msg
                
            logger.warning(f"No changes made for project {project_id} - project might be in invalid state")
            execute_query("ROLLBACK")
            return False, "Failed to delete project - no changes made"
            
        except Exception as e:
            execute_query("ROLLBACK")
            error_msg = f"Database error while deleting project: {str(e)}"
            logger.error(f"{error_msg}\nProject ID: {project_id}\nProject Name: {project_name}")
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Error accessing project: {str(e)}"
        logger.error(f"{error_msg}\nProject ID: {project_id}")
        return False, error_msg

def restore_project(project_id):
    """Restore a soft-deleted project and its tasks"""
    try:
        execute_query("BEGIN")
        result = execute_query("""
            UPDATE projects 
            SET deleted_at = NULL 
            WHERE id = %s AND deleted_at IS NOT NULL
            RETURNING id
        """, (project_id,))
        
        if result:
            # Restore all associated tasks
            execute_query("""
                UPDATE tasks 
                SET deleted_at = NULL 
                WHERE project_id = %s AND deleted_at IS NOT NULL
            """, (project_id,))
            
            execute_query("COMMIT")
            # Clear cache after successful restoration
            if 'query_cache' in st.session_state:
                st.session_state.query_cache.clear()
            return True
            
        execute_query("ROLLBACK")
        return False
    except Exception as e:
        execute_query("ROLLBACK")
        logger.error(f"Error restoring project: {str(e)}")
        return False

def get_deleted_projects():
    """Get list of deleted projects with task counts"""
    try:
        return execute_query('''
            SELECT p.*,
                   COUNT(t.id) as total_tasks,
                   COUNT(CASE WHEN t.status = 'Done' THEN 1 END) as completed_tasks
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            WHERE p.deleted_at IS NOT NULL
            GROUP BY p.id
            ORDER BY p.deleted_at DESC
        ''')
    except Exception as e:
        logger.error(f"Error fetching deleted projects: {str(e)}")
        return []

def create_project_form():
    """Create new project form"""
    # Initialize show_form in session state if not exists
    if 'show_project_form' not in st.session_state:
        st.session_state.show_project_form = False
    
    # Add button to toggle form visibility
    if not st.session_state.show_project_form:
        if st.button("➕ Create New Project"):
            st.session_state.show_project_form = True
            st.rerun()
        return False

    # Show form with cancel button when visible
    with st.form("project_form"):
        st.write("### Create Project")
        
        name = st.text_input("Project Name")
        description = st.text_area("Description")
        deadline = st.date_input("Deadline")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Create Project")
        with col2:
            cancelled = st.form_submit_button("Cancel")
        
        if cancelled:
            st.session_state.show_project_form = False
            st.rerun()
            return False
            
        if submitted:
            if not name:
                st.error("Project name is required!")
                return False
                
            try:
                execute_query("BEGIN")
                result = execute_query('''
                    INSERT INTO projects (name, description, deadline, created_at, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id, name
                    ''',
                    (name, description, deadline)
                )
                
                if result:
                    execute_query("COMMIT")
                    st.success(f"Project '{name}' created successfully!")
                    st.session_state.show_project_form = False
                    time.sleep(0.5)
                    return True
                    
                execute_query("ROLLBACK")
                st.error("Failed to create project - database error")
                return False
                    
            except Exception as e:
                execute_query("ROLLBACK")
                logger.error(f"Error creating project: {str(e)}")
                st.error(f"Error creating project: {str(e)}")
                return False
    return False

def edit_project_form(project_id):
    """Edit project form"""
    try:
        # Get current project data
        project = execute_query("""
            SELECT p.*, 
                COUNT(t.id) as total_tasks,
                COUNT(CASE WHEN t.status = 'Done' THEN 1 END) as completed_tasks
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id AND t.deleted_at IS NULL
            WHERE p.id = %s AND p.deleted_at IS NULL
            GROUP BY p.id
        """, (project_id,))
        
        if not project:
            st.error("Project not found!")
            return False
            
        project = convert_project_dates(project[0])
        
        with st.form(key=f"edit_project_form_{project_id}"):
            st.write("### Edit Project")
            
            name = st.text_input("Project Name", value=project['name'])
            description = st.text_area("Description", value=project['description'] or "")
            current_deadline = datetime.fromisoformat(project['deadline']).date() if project['deadline'] else None
            deadline = st.date_input("Deadline", value=current_deadline)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                save_button = st.form_submit_button("Save Changes")
            with col2:
                cancel_button = st.form_submit_button("Cancel")
            
            if cancel_button:
                st.session_state.editing_project = None
                return True
                
            if save_button:
                if not name:
                    st.error("Project name cannot be empty!")
                    return False
                
                try:
                    execute_query('BEGIN')
                    result = execute_query('''
                        UPDATE projects 
                        SET name = %s, 
                            description = %s, 
                            deadline = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND deleted_at IS NULL
                        RETURNING id
                    ''', (name, description, deadline, project_id))
                    
                    if result:
                        execute_query('COMMIT')
                        st.success("Project updated successfully!")
                        st.session_state.editing_project = None
                        time.sleep(0.5)
                        return True
                    
                    execute_query('ROLLBACK')
                    st.error("Failed to update project")
                    return False
                    
                except Exception as e:
                    execute_query('ROLLBACK')
                    logger.error(f"Error updating project: {str(e)}")
                    st.error(f"Error updating project: {str(e)}")
                    return False
                    
        return False
        
    except Exception as e:
        logger.error(f"Error in edit form: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        return False

def list_projects():
    """List all projects with edit functionality"""
    try:
        # Initialize editing_project in session state if not exists
        if 'editing_project' not in st.session_state:
            st.session_state.editing_project = None
            
        # Initialize show_deleted_projects in session state if not exists
        if 'show_deleted_projects' not in st.session_state:
            st.session_state.show_deleted_projects = False
            
        # Get active projects with task counts
        projects = execute_query('''
            SELECT p.*,
                   COUNT(t.id) as total_tasks,
                   COUNT(CASE WHEN t.status = 'Done' THEN 1 END) as completed_tasks
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            WHERE p.deleted_at IS NULL
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''')
        
        selected_project = None
        
        # Process datetime fields and display active projects
        if projects:
            logger.info(f"Processing {len(projects)} active projects")
            projects = [convert_project_dates(project) for project in projects]
            
            st.write("### Active Projects")
            for project in projects:
                with st.container():
                    col1, col2, col3, col4 = st.columns([6, 2, 1, 1])
                    
                    with col1:
                        if st.button(
                            f"{project['name']} ({project['completed_tasks']}/{project['total_tasks']} tasks)",
                            key=f"select_project_{project['id']}"
                        ):
                            selected_project = project['id']
                            
                    with col2:
                        deadline_str = datetime.fromisoformat(project['deadline']).strftime('%d/%m/%Y') if project['deadline'] else 'No deadline'
                        st.write(f"Due: {deadline_str}")
                            
                    with col3:
                        if st.button("✏️", key=f"edit_project_{project['id']}", help="Edit project"):
                            st.session_state.editing_project = project['id']
                            
                    with col4:
                        if st.button("🗑️", key=f"delete_project_{project['id']}", help="Delete project"):
                            if st.button("Confirm Delete", key=f"confirm_delete_{project['id']}"):
                                success, message = delete_project(project['id'])
                                if success:
                                    st.success(message)
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error(message)
                                
                    # Show edit form if this project is being edited
                    if st.session_state.get('editing_project') == project['id']:
                        if edit_project_form(project['id']):
                            st.rerun()
        else:
            st.info("No active projects found. Create one to get started!")
        
        # Display deleted projects section with improved visibility
        deleted_projects = get_deleted_projects()
        if deleted_projects:
            st.markdown("""
                <div style="margin-top: 2rem; border-top: 1px solid #eee; padding-top: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3 style="margin: 0; color: #666;">Deleted Projects</h3>
                        <span style="color: #666; font-size: 0.9em; background: #f1f5f9; padding: 2px 8px; border-radius: 4px;">
                            {} project{} in trash
                        </span>
                    </div>
                </div>
            """.format(len(deleted_projects), 's' if len(deleted_projects) != 1 else ''), unsafe_allow_html=True)
            
            # Add expand/collapse functionality with styled checkbox
            if st.checkbox("📂 Show deleted projects", key="show_deleted_projects", help="Click to show/hide deleted projects"):
                st.markdown("""
                    <div class="deleted-projects-section" style="background: #f8fafc; border: 1px solid #eee; border-radius: 4px; padding: 1rem; margin-top: 0.5rem;">
                """, unsafe_allow_html=True)
                
                for project in deleted_projects:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([6, 2, 1, 1])
                        
                        with col1:
                            st.markdown(f"""
                                <div class="project-title" style="color: #4b5563;">
                                    {project['name']}
                                    <span class="task-count" style="color: #6b7280; font-size: 0.9em; margin-left: 0.5rem;">
                                        ({project['completed_tasks']}/{project['total_tasks']} tasks)
                                    </span>
                                </div>
                            """, unsafe_allow_html=True)
                            
                        with col2:
                            deadline_str = datetime.fromisoformat(project['deadline']).strftime('%d/%m/%Y') if project['deadline'] else 'No deadline'
                            st.markdown(f"""
                                <div class="project-deadline" style="color: #6b7280; text-align: center;">
                                    Due: {deadline_str}
                                </div>
                            """, unsafe_allow_html=True)
                            
                        with col3:
                            restore_key = f"restore_project_{project['id']}"
                            if st.button("🔄", key=restore_key, help="Restore project"):
                                try:
                                    if restore_project(project['id']):
                                        st.success(f"Project '{project['name']}' restored successfully")
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.error("Failed to restore project. Please try again.")
                                except Exception as e:
                                    logger.error(f"Error restoring project {project['id']}: {str(e)}")
                                    st.error("An error occurred while restoring the project")
                                    
                        with col4:
                            delete_key = f"delete_project_{project['id']}"
                            confirm_key = f"confirm_delete_{project['id']}"
                            
                            if delete_key not in st.session_state:
                                st.session_state[delete_key] = False
                                
                            if st.button("⛔", key=delete_key, help="Permanently delete"):
                                st.session_state[delete_key] = True
                                
                            if st.session_state[delete_key]:
                                st.markdown("""
                                    <div style="background: #fee2e2; border: 1px solid #ef4444; border-radius: 4px; padding: 0.5rem; margin: 0.5rem 0;">
                                        <p style="color: #991b1b; margin: 0; font-size: 0.9em;">This action cannot be undone.</p>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("✓ Confirm", key=f"confirm_{confirm_key}"):
                                        try:
                                            if delete_project(project['id'], permanent=True):
                                                st.success(f"Project '{project['name']}' permanently deleted")
                                                st.session_state[delete_key] = False
                                                time.sleep(0.5)
                                                st.rerun()
                                            else:
                                                st.error("Failed to delete project. Please try again.")
                                        except Exception as e:
                                            logger.error(f"Error deleting project {project['id']}: {str(e)}")
                                            st.error("An error occurred while deleting the project")
                                with col2:
                                    if st.button("✗ Cancel", key=f"cancel_{confirm_key}"):
                                        st.session_state[delete_key] = False
                                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Add a note about permanent deletion
                st.markdown("""
                    <div style="margin-top: 1rem; padding: 0.5rem; border-left: 3px solid #cbd5e1; background: #f8fafc;">
                        <p style="color: #64748b; margin: 0; font-size: 0.9em;">
                            ℹ️ Permanently deleted projects cannot be recovered.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                                    
        return selected_project
        
    except Exception as e:
        logger.error(f"Error in list_projects: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        return None

if __name__ == "__main__":
    selected_project = list_projects()
    if selected_project:
        create_project_form()
