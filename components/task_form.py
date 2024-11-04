import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging
from utils.file_handler import save_uploaded_file

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        with st.form("task_form"):
            title = st.text_input("Task Title")
            description = st.text_area("Description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            due_date = st.date_input("Due Date", min_value=datetime.today())
            
            # File upload field
            uploaded_file = st.file_uploader("Attach File", 
                type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx'])
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("Task title is required!")
                    return False
                    
                try:
                    # Insert task
                    result = execute_query('''
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, due_date)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (project_id, title, description, status, priority, due_date))
                    
                    if result:
                        task_id = result[0]['id']
                        
                        # Handle file upload if present
                        if uploaded_file:
                            attachment_id = save_uploaded_file(uploaded_file, task_id)
                            if attachment_id is None:
                                logger.error("Failed to save file attachment")
                                st.error("Failed to save file attachment")
                                return False
                        
                        st.success(f"Task '{title}' created successfully!")
                        st.rerun()
                        return True
                        
                    st.error("Failed to create task")
                    return False
                    
                except Exception as e:
                    logger.error(f"Error creating task: {str(e)}")
                    st.error(f"Error creating task: {str(e)}")
                    return False
                    
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error(f"Form error: {str(e)}")
        return False
