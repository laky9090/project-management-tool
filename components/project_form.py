import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

def create_project_form():
    with st.form("project_form"):
        st.write("### Create Project")
        
        name = st.text_input("Project Name")
        description = st.text_area("Description")
        deadline = st.date_input("Deadline", min_value=datetime.today())
        
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
                    st.session_state.current_view = 'Board'
                    time.sleep(0.5)
                    st.rerun()
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
        
        # Store original values in session state for comparison
        if 'original_project_values' not in st.session_state:
            st.session_state.original_project_values = {
                'name': project['name'],
                'description': project['description'],
                'deadline': project['deadline']
            }
        
        with st.form(key=f"edit_project_form_{project_id}"):
            st.write("### Edit Project")
            
            name = st.text_input("Project Name", value=project['name'])
            description = st.text_area("Description", value=project['description'] or "")
            deadline = st.date_input("Deadline", value=project['deadline'] if project['deadline'] else datetime.today())
            
            col1, col2 = st.columns([1, 1])
            with col1:
                save_button = st.form_submit_button("Save Changes")
            with col2:
                cancel_button = st.form_submit_button("Cancel")
            
            if cancel_button:
                del st.session_state.original_project_values
                st.session_state.editing_project = None
                return True
                
            if save_button:
                if not name:
                    st.error("Project name cannot be empty!")
                    return False
                    
                # Check if any changes were made
                if (name == st.session_state.original_project_values['name'] and
                    description == st.session_state.original_project_values['description'] and
                    deadline == st.session_state.original_project_values['deadline']):
                    st.warning("No changes were made.")
                    st.session_state.editing_project = None
                    return True
                
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
                        # Clear the original values from session state
                        del st.session_state.original_project_values
                        st.session_state.editing_project = None
                        time.sleep(0.5)  # Add delay to ensure message is visible
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
        projects = execute_query('''
            SELECT p.*,
                   COUNT(t.id) as total_tasks,
                   COUNT(CASE WHEN t.status = 'Done' THEN 1 END) as completed_tasks
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''')
        
        selected_project = None
        
        if projects:
            for project in projects:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        # Project name and progress
                        if st.button(
                            f"{project['name']} ({project['completed_tasks']}/{project['total_tasks']} tasks)",
                            key=f"select_project_{project['id']}"
                        ):
                            selected_project = project['id']
                            
                    with col2:
                        # Deadline with French date format
                        st.write(f"Due: {project['deadline'].strftime('%d/%m/%Y') if project['deadline'] else 'No deadline'}")
                        
                    with col3:
                        # Edit button
                        if st.button("✏️", key=f"edit_project_{project['id']}"):
                            st.session_state.editing_project = project['id']
                            
                    # Show edit form if this project is being edited
                    if st.session_state.get('editing_project') == project['id']:
                        if edit_project_form(project['id']):
                            st.rerun()
            
            return selected_project
        else:
            st.info("No projects found. Create one to get started!")
        
        return selected_project
        
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        st.error(f"Error loading projects: {str(e)}")
        return None
