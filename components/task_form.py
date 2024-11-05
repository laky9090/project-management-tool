import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging
import os

logger = logging.getLogger(__name__)

def create_task_form(project_id, on_task_created=None):
    try:
        with st.form("task_form", clear_on_submit=True):
            st.write("### Create Task")
            
            # Form fields
            title = st.text_input("Title")
            description = st.text_area("Description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            due_date = st.date_input("Due Date")
            
            # File upload field with accepted types
            uploaded_file = st.file_uploader(
                "Attach File",
                type=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'],
                help="Upload a file (max 200MB)"
            )
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("Title is required")
                    return False
                
                try:
                    # Ensure uploads directory exists
                    os.makedirs('uploads', exist_ok=True)
                    
                    # Create task
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status, priority, due_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id, title, status;
                    ''', (project_id, title, description, status, priority, due_date))
                    
                    if result:
                        task_id = result[0]['id']
                        success_message = f"Task '{title}' created successfully!"
                        
                        # Handle file upload if present
                        if uploaded_file:
                            try:
                                file_id = save_uploaded_file(uploaded_file, task_id)
                                if file_id:
                                    success_message += f"\nFile '{uploaded_file.name}' attached successfully!"
                                else:
                                    st.warning(f"Failed to attach file '{uploaded_file.name}', but task was created")
                            except Exception as e:
                                logger.error(f"File upload error: {str(e)}")
                                st.warning(f"Failed to upload file: {str(e)}")
                        
                        st.success(success_message)
                        
                        # Call callback if provided
                        if on_task_created:
                            on_task_created()
                        
                        st.rerun()
                        return True
                    
                    st.error("Failed to create task")
                    return False
                    
                except Exception as e:
                    logger.error(f"Task creation error: {str(e)}")
                    st.error(f"Error creating task: {str(e)}")
                    return False
    
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error(f"Form error: {str(e)}")
        return False
