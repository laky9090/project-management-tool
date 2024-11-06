import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging

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
    project = execute_query('SELECT * FROM projects WHERE id = %s', (project_id,))[0]
    
    with st.form("edit_project_form"):
        name = st.text_input("Project Name", value=project['name'])
        description = st.text_area("Description", value=project['description'])
        deadline = st.date_input("Deadline", value=project['deadline'])
        
        if st.form_submit_button("Save Changes"):
            try:
                execute_query('''
                    UPDATE projects 
                    SET name = %s, description = %s, deadline = %s
                    WHERE id = %s
                ''', (name, description, deadline, project_id))
                st.success("Project updated successfully!")
                st.rerun()
                return True
            except Exception as e:
                st.error(f"Error updating project: {str(e)}")
                return False
    return False

def list_projects():
    projects = execute_query('''
        SELECT p.*
        FROM projects p
        ORDER BY p.created_at DESC
    ''')
    
    selected_project = None
    
    if projects:
        # Add edit button for each project
        for project in projects:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"{project['name']} - Due: {project['deadline'].strftime('%b %d, %Y') if project['deadline'] else 'No deadline'}", 
                           key=f"select_project_{project['id']}"):
                    selected_project = project['id']
            with col2:
                if st.button("✏️", key=f"edit_project_{project['id']}"):
                    edit_project_form(project['id'])
        
        return selected_project
    else:
        st.info("No projects found. Create one to get started!")
    
    return selected_project
