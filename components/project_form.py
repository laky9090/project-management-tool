import streamlit as st
from database.connection import execute_query
from datetime import datetime

def create_project_form():
    with st.form("project_form"):
        st.write("Create New Project")
        name = st.text_input("Project Name")
        description = st.text_area("Description")
        deadline = st.date_input("Deadline", min_value=datetime.today())
        
        submitted = st.form_submit_button("Create Project")
        
        if submitted and name:
            execute_query(
                "INSERT INTO projects (name, description, deadline) VALUES (%s, %s, %s)",
                (name, description, deadline)
            )
            st.success("Project created successfully!")
            return True
    return False

def list_projects():
    projects = execute_query("SELECT * FROM projects ORDER BY created_at DESC")
    if projects:
        for project in projects:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"### {project['name']}")
                st.write(project['description'])
            with col2:
                st.write(f"Deadline: {project['deadline']}")
                if st.button("Select", key=f"project_{project['id']}"):
                    return project['id']
    else:
        st.info("No projects found. Create one to get started!")
    return None
