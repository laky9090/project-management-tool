import streamlit as st
from database.connection import execute_query
import logging
import time

logger = logging.getLogger(__name__)

def delete_project(project_id):
    try:
        result = execute_query(
            "UPDATE projects SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id",
            (project_id,)
        )
        return bool(result)
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        return False

def restore_project(project_id):
    try:
        result = execute_query(
            "UPDATE projects SET deleted_at = NULL WHERE id = %s RETURNING id",
            (project_id,)
        )
        return bool(result)
    except Exception as e:
        logger.error(f"Error restoring project: {str(e)}")
        return False

def get_deleted_projects():
    return execute_query(
        "SELECT * FROM projects WHERE deleted_at IS NOT NULL ORDER BY created_at DESC"
    )

def create_project_form():
    """Create new project form"""
    with st.form("project_form"):
        st.write("### Create Project")
        
        name = st.text_input("Project Name")
        description = st.text_area("Description")
        deadline = st.date_input("Deadline")
        
        submitted = st.form_submit_button("Create Project")
        
        if submitted and name:
            try:
                result = execute_query(
                    '''
                    INSERT INTO projects (name, description, deadline)
                    VALUES (%s, %s, %s)
                    RETURNING id, name
                    ''',
                    (name, description, deadline)
                )
                
                if result:
                    st.success(f"Project '{name}' created successfully!")
                    time.sleep(0.5)
                    return True
                    
                st.error("Failed to create project - database error")
                return False
                    
            except Exception as e:
                logger.error(f"Error creating project: {str(e)}")
                st.error(f"Error creating project: {str(e)}")
                return False
    return False

def edit_project_form(project_id):
    """Edit project form"""
    try:
        # Get current project data
        project = execute_query('SELECT * FROM projects WHERE id = %s', (project_id,))
        if not project:
            st.error("Project not found!")
            return False
            
        project = project[0]
        
        with st.form(key=f"edit_project_form_{project_id}"):
            st.write("### Edit Project")
            
            name = st.text_input("Project Name", value=project['name'])
            description = st.text_area("Description", value=project['description'] or "")
            deadline = st.date_input("Deadline", value=project['deadline'] if project['deadline'] else None)
            
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
                        SET name = %s, description = %s, deadline = %s
                        WHERE id = %s
                        RETURNING id
                    ''', (name, description, deadline, project_id))
                    
                    if result:
                        execute_query('COMMIT')
                        st.success("Project updated successfully!")
                        st.session_state.editing_project = None
                        time.sleep(0.5)
                        return True
                    else:
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
        # Get active projects
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
        
        # Display active projects
        if projects:
            st.write("### Active Projects")
            for project in projects:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        if st.button(
                            f"{project['name']} ({project['completed_tasks']}/{project['total_tasks']} tasks)",
                            key=f"select_project_{project['id']}"
                        ):
                            selected_project = project['id']
                            
                    with col2:
                        st.write(f"Due: {project['deadline'].strftime('%d/%m/%Y') if project['deadline'] else 'No deadline'}")
                        
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
                    
                    # Show edit form if this project is being edited
                    if st.session_state.get('editing_project') == project['id']:
                        if edit_project_form(project['id']):
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
                        st.write(f"{project['name']} (Deleted on: {project['deleted_at'].strftime('%d/%m/%Y')})")
                        
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
