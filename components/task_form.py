import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        with st.form("task_form"):
            st.write("### Create Task")
            st.write(f"Creating task for project: {project_id}")
            
            title = st.text_input("Title")
            description = st.text_area("Description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            
            # Add file upload field
            uploaded_file = st.file_uploader("Attach File", type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx'])
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted and title:
                # Debug: Show what we're about to insert
                st.write("Debug: Task data to insert:")
                st.json({
                    "project_id": project_id,
                    "title": title,
                    "description": description,
                    "status": status,
                    "has_attachment": uploaded_file is not None
                })
                
                result = execute_query('''
                    INSERT INTO tasks (project_id, title, description, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, title, status, created_at;
                ''', (project_id, title, description, status))
                
                if result:
                    task_id = result[0]['id']
                    st.success("Task created successfully!")
                    st.write("Debug: Created task data:", result[0])
                    
                    # Handle file upload if present
                    if uploaded_file:
                        attachment_id = save_uploaded_file(uploaded_file, task_id)
                        if attachment_id:
                            st.success(f"File '{uploaded_file.name}' attached successfully")
                            st.write("Debug: Created attachment with ID:", attachment_id)
                        else:
                            st.warning("Failed to save file attachment")
                    
                    st.rerun()
                    return True
                    
                st.error("Failed to create task")
                return False
                
        return False
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False
