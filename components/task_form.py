import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    with st.form("task_form"):
        st.write("### Create Task")
        st.write(f"Creating task for project: {project_id}")
        
        title = st.text_input("Title")
        description = st.text_area("Description")
        status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
        
        # Simple file upload
        uploaded_file = st.file_uploader("Attach File", type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx'])
        
        submitted = st.form_submit_button("Create Task")
        
        if submitted and title:
            try:
                # Debug information
                st.write("### Debug Info")
                st.write(f"Creating task with title: {title}")
                
                # Simple insert without transaction
                result = execute_query('''
                    INSERT INTO tasks (project_id, title, description, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, title, status;
                ''', (project_id, title, description, status))
                
                if result:
                    task_id = result[0]['id']
                    st.success(f"Task '{title}' created successfully!")
                    st.write("Created task:", result[0])
                    
                    # Handle file upload if present
                    if uploaded_file:
                        attachment_id = save_uploaded_file(uploaded_file, task_id)
                        if attachment_id:
                            st.success(f"File '{uploaded_file.name}' attached successfully")
                        else:
                            st.warning("Failed to save file attachment")
                    
                    st.rerun()
                    return True
                
                st.error("Failed to create task")
                return False
                
            except Exception as e:
                logger.error(f"Error creating task: {str(e)}")
                st.error(f"Error: {str(e)}")
                return False
    return False
