import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    logger.info(f"Creating task form for project {project_id}")
    
    with st.form("task_form", clear_on_submit=True):
        st.write("### Create Task")
        st.write(f"Creating task for project ID: {project_id}")
        
        title = st.text_input("Title")
        description = st.text_area("Description")
        status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
        
        # Add file upload field
        uploaded_file = st.file_uploader("Attach File", type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx'])
        
        submitted = st.form_submit_button("Create Task")
        
        if submitted and title:
            try:
                # Debug information
                st.write("### Debug Info")
                st.write(f"Creating task with title: {title}")
                if uploaded_file:
                    st.write(f"File to be attached: {uploaded_file.name}")
                
                # Start transaction
                execute_query("BEGIN")
                
                # Create task
                result = execute_query('''
                    INSERT INTO tasks (project_id, title, description, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, title;
                ''', (project_id, title, description, status))
                
                if result:
                    task_id = result[0]['id']
                    
                    # Handle file upload if present
                    if uploaded_file:
                        logger.info(f"Saving attachment for task {task_id}")
                        attachment_id = save_uploaded_file(uploaded_file, task_id)
                        if attachment_id is None:
                            execute_query("ROLLBACK")
                            st.error("Failed to save file attachment")
                            return False
                    
                    execute_query("COMMIT")
                    st.success(f"Task '{title}' created successfully!")
                    if uploaded_file:
                        st.success(f"File '{uploaded_file.name}' attached to the task")
                    st.rerun()
                    return True
                
                execute_query("ROLLBACK")
                st.error("Failed to create task")
                return False
                
            except Exception as e:
                execute_query("ROLLBACK")
                logger.error(f"Error creating task: {str(e)}")
                st.error(f"Error: {str(e)}")
                return False
    return False
