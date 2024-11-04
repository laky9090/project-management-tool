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
    selected_project = None
    
    if projects:
        for project in projects:
            with st.container():
                selected = st.session_state.get('selected_project') == project['id']
                card_style = '''
                    padding: 1rem;
                    border-radius: 8px;
                    margin-bottom: 0.5rem;
                    background: white;
                    border: 2px solid;
                    border-color: {} !important;
                    cursor: pointer;
                    transition: transform 0.2s ease, box-shadow 0.2s ease;
                    &:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    }}
                '''.format('#7C3AED' if selected else '#E5E7EB')
                
                st.markdown(f'''
                    <div style="{card_style}">
                        <h3 style="margin: 0; color: #1F2937;">{project['name']}</h3>
                        <p style="margin: 0.5rem 0; color: #4B5563;">{project['description'] if project['description'] else 'No description'}</p>
                        <div style="color: #6B7280">Due: {project['deadline'].strftime('%b %d, %Y') if project['deadline'] else 'No deadline'}</div>
                    </div>
                ''', unsafe_allow_html=True)
                
                if st.button("Select", key=f"project_{project['id']}", use_container_width=True):
                    selected_project = project['id']
    else:
        st.info("No projects found. Create one to get started!")
    
    return selected_project
