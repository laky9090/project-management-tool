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

def delete_project(project_id):
    """Delete project (soft delete) and all its tasks"""
    try:
        # Start transaction
        execute_query("BEGIN")
        
        # Update project
        result = execute_query("""
            UPDATE projects 
            SET deleted_at = CURRENT_TIMESTAMP, 
                updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s AND deleted_at IS NULL 
            RETURNING id
        """, (project_id,))
        
        if result:
            # Also mark all project tasks as deleted
            execute_query("""
                UPDATE tasks 
                SET deleted_at = CURRENT_TIMESTAMP 
                WHERE project_id = %s AND deleted_at IS NULL
            """, (project_id,))
            
            # Commit transaction
            execute_query("COMMIT")
            logger.info(f"Project {project_id} and its tasks deleted successfully")
            return True
        
        # Rollback if no rows affected
        execute_query("ROLLBACK")
        return False
    except Exception as e:
        execute_query("ROLLBACK")
        logger.error(f"Error deleting project: {str(e)}")
        return False

def restore_project(project_id):
    """Restore deleted project and optionally its tasks"""
    try:
        # Start transaction
        execute_query("BEGIN")
        
        # Restore project
        result = execute_query("""
            UPDATE projects 
            SET deleted_at = NULL, 
                updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s AND deleted_at IS NOT NULL 
            RETURNING id
        """, (project_id,))
        
        if result:
            # Also restore project tasks
            execute_query("""
                UPDATE tasks 
                SET deleted_at = NULL 
                WHERE project_id = %s AND deleted_at IS NOT NULL
            """, (project_id,))
            
            # Commit transaction
            execute_query("COMMIT")
            logger.info(f"Project {project_id} and its tasks restored successfully")
            return True
            
        # Rollback if no rows affected
        execute_query("ROLLBACK")
        return False
    except Exception as e:
        execute_query("ROLLBACK")
        logger.error(f"Error restoring project: {str(e)}")
        return False

def get_deleted_projects():
    """Get all deleted projects with task counts"""
    try:
        projects = execute_query("""
            SELECT p.*, 
                COUNT(t.id) as total_tasks,
                COUNT(CASE WHEN t.status = 'Done' THEN 1 END) as completed_tasks
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            WHERE p.deleted_at IS NOT NULL
            GROUP BY p.id
            ORDER BY p.deleted_at DESC
        """)
        
        if projects:
            projects = [convert_project_dates(project) for project in projects]
            logger.info(f"Successfully retrieved and converted {len(projects)} deleted projects")
        return projects
    except Exception as e:
        logger.error(f"Error getting deleted projects: {str(e)}")
        return []

def create_project_form():
    """Create new project form"""
    with st.form("project_form"):
        st.write("### Create Project")
        
        name = st.text_input("Project Name")
        description = st.text_area("Description")
        deadline = st.date_input("Deadline")
        
        submitted = st.form_submit_button("Create Project")
        
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
            
        # Get active projects with task counts
        projects = execute_query('''
            SELECT p.*,
                   COUNT(t.id) as total_tasks,
                   COUNT(CASE WHEN t.status = 'Done' THEN 1 END) as completed_tasks
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id AND t.deleted_at IS NULL
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
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                    
                    with col1:
                        if st.button(
                            f"{project['name']} ({project['completed_tasks']}/{project['total_tasks']} tasks)",
                            key=f"select_project_{project['id']}"
                        ):
                            selected_project = project['id']
                            
                    with col2:
                        try:
                            deadline_str = datetime.fromisoformat(project['deadline']).strftime('%d/%m/%Y') if project['deadline'] else 'No deadline'
                            st.write(f"Due: {deadline_str}")
                        except Exception as e:
                            logger.error(f"Error formatting deadline for project {project['id']}: {str(e)}")
                            st.write("Due: Invalid date")
                            
                    with col3:
                        if st.button("✏️", key=f"edit_project_{project['id']}", help="Edit project"):
                            st.session_state.editing_project = project['id']
                            
                    with col4:
                        if st.button("🗑️", key=f"delete_project_{project['id']}", help="Delete project"):
                            if delete_project(project['id']):
                                st.success(f"Project '{project['name']}' deleted")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Failed to delete project")
                    
                    with col5:
                        if st.button("🔄", key=f"restore_project_{project['id']}", help="Restore project"):
                            if restore_project(project['id']):
                                st.success(f"Project '{project['name']}' restored")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Failed to restore project")
                                
                    # Show edit form if this project is being edited
                    if st.session_state.get('editing_project') == project['id']:
                        name = st.text_input("Name", value=project['name'])
                        description = st.text_area("Description", value=project['description'] or "")
                        current_deadline = datetime.fromisoformat(project['deadline']).date() if project['deadline'] else None
                        deadline = st.date_input("Deadline", value=current_deadline)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Save", key=f"save_project_{project['id']}"):
                                if not name:
                                    st.error("Project name cannot be empty!")
                                else:
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
                                        ''', (name, description, deadline, project['id']))
                                        
                                        if result:
                                            execute_query('COMMIT')
                                            st.success("Project updated successfully!")
                                            st.session_state.editing_project = None
                                            time.sleep(0.5)
                                            st.rerun()
                                        else:
                                            execute_query('ROLLBACK')
                                            st.error("Failed to update project")
                                    except Exception as e:
                                        execute_query('ROLLBACK')
                                        logger.error(f"Error updating project: {str(e)}")
                                        st.error(f"Error updating project: {str(e)}")
                        
                        with col2:
                            if st.button("Cancel", key=f"cancel_edit_{project['id']}"):
                                st.session_state.editing_project = None
                                st.rerun()
        else:
            st.info("No active projects found. Create one to get started!")
        
        # Display deleted projects
        deleted_projects = get_deleted_projects()
        if deleted_projects:
            st.write("### Deleted Projects")
            for project in deleted_projects:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        try:
                            deleted_date = datetime.fromisoformat(project['deleted_at']).strftime('%d/%m/%Y') if project['deleted_at'] else 'Unknown'
                            st.write(f"{project['name']} (Deleted on: {deleted_date})")
                        except Exception as e:
                            logger.error(f"Error formatting deleted date for project {project.get('id')}: {str(e)}")
                            st.write(f"{project['name']} (Deleted on: Unknown)")
                        
                    with col2:
                        if st.button("🔄", key=f"restore_project_{project['id']}", help="Restore project"):
                            if restore_project(project['id']):
                                st.success(f"Project '{project['name']}' restored")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Failed to restore project")
        
        return selected_project
        
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        st.error(f"Error loading projects: {str(e)}")
        return None