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

def list_projects():
    projects = execute_query('''
        SELECT p.*
        FROM projects p
        ORDER BY p.created_at DESC
    ''')
    
    selected_project = None
    
    if projects:
        # Convert projects to list for selectbox
        project_options = [(p['id'], f"{p['name']} - Due: {p['deadline'].strftime('%b %d, %Y') if p['deadline'] else 'No deadline'}") for p in projects]
        
        selected_id = st.selectbox(
            "Select Project",
            options=project_options,
            format_func=lambda x: x[1],
            key="project_selector"
        )
        
        # Return the selected project ID
        return selected_id[0] if selected_id else None
    else:
        st.info("No projects found. Create one to get started!")
    
    return selected_project
