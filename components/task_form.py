import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging
import os

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        st.write("### Create Task")
        
        with st.form("task_form", clear_on_submit=True):
            # Form fields
            title = st.text_input("Title", key="task_title")
            description = st.text_area("Description", key="task_desc")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"], key="task_status")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"], key="task_priority")
            due_date = st.date_input("Due Date", key="task_due_date")
            
            # File upload field with clear instructions
            uploaded_file = st.file_uploader(
                "Attach File",
                type=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'],
                help="Upload a file (max 200MB)",
                key="task_file"
            )
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("Title is required")
                    return False
                    
                try:
                    # Start transaction
                    execute_query('BEGIN')
                    
                    # Create task
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status, priority, due_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING *;
                    ''', (project_id, title, description, status, priority, due_date))
                    
                    if result:
                        task_id = result[0]['id']
                        
                        # Handle file upload if present
                        file_id = None
                        if uploaded_file:
                            try:
                                os.makedirs('uploads', exist_ok=True)
                                file_id = save_uploaded_file(uploaded_file, task_id)
                                if not file_id:
                                    st.warning("Failed to save file attachment, but task was created")
                            except Exception as e:
                                logger.error(f"File upload error: {str(e)}")
                                st.warning(f"Failed to upload file: {str(e)}")
                        
                        execute_query('COMMIT')
                        
                        success_message = f"Task '{title}' created successfully!"
                        if file_id:
                            success_message += f"\nFile '{uploaded_file.name}' attached."
                        st.success(success_message)
                        
                        # Force refresh
                        st.rerun()
                        return True
                    
                    execute_query('ROLLBACK')
                    st.error("Failed to create task - database error")
                    return False
                    
                except Exception as e:
                    execute_query('ROLLBACK')
                    logger.error(f"Task creation error: {str(e)}")
                    st.error(f"Error creating task: {str(e)}")
                    return False
                    
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error(f"Form error: {str(e)}")
        return False
