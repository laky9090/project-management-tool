import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_project_form():
    with st.form("project_form"):
        st.write("Create New Project")
        name = st.text_input("Project Name")
        description = st.text_area("Description")
        deadline = st.date_input("Deadline", min_value=datetime.today())
        
        submitted = st.form_submit_button("Create Project")
        
        if submitted and name:
            try:
                # Start transaction
                execute_query("BEGIN")
                
                # Create project with owner
                result = execute_query(
                    """
                    INSERT INTO projects (name, description, deadline, owner_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (name, description, deadline, st.session_state.user_id)
                )
                
                if result:
                    project_id = result[0]['id']
                    # Add creator as project admin
                    execute_query(
                        """
                        INSERT INTO project_members (project_id, user_id, role)
                        VALUES (%s, %s, %s)
                        """,
                        (project_id, st.session_state.user_id, 'project_admin')
                    )
                    
                    execute_query("COMMIT")
                    st.success("Project created successfully!")
                    return True
                else:
                    execute_query("ROLLBACK")
                    st.error("Failed to create project!")
            except Exception as e:
                execute_query("ROLLBACK")
                logger.error(f"Error creating project: {str(e)}")
                st.error(f"Error creating project: {str(e)}")
                return False
    return False

def list_projects():
    # Get projects where user is a member
    projects = execute_query("""
        SELECT p.*, pm.role as user_role
        FROM projects p
        JOIN project_members pm ON p.id = pm.project_id
        WHERE pm.user_id = %s
        ORDER BY p.created_at DESC
    """, (st.session_state.user_id,))
    
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
                        <div style="color: #6B7280">Role: {project['user_role']}</div>
                    </div>
                ''', unsafe_allow_html=True)
                
                if st.button("Select", key=f"project_{project['id']}", use_container_width=True):
                    selected_project = project['id']
    else:
        st.info("No projects found. Create one to get started!")
    
    return selected_project
