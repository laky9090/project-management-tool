import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging
from utils.file_handler import save_uploaded_file

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    with st.form("task_form"):
        title = st.text_input("Task Title")
        description = st.text_area("Description")
        status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        
        # File upload field
        uploaded_file = st.file_uploader("Attach File", 
            type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx'])
        
        submitted = st.form_submit_button("Create Task")
        
        if submitted and title:
            try:
                result = execute_query('''
                    INSERT INTO tasks (project_id, title, description, status, priority)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                ''', (project_id, title, description, status, priority))
                
                if result:
                    task_id = result[0]['id']
                    
                    # Handle file upload if present
                    if uploaded_file:
                        attachment_id = save_uploaded_file(uploaded_file, task_id)
                        if attachment_id is None:
                            st.error("Failed to save file attachment")
                            return False
                    
                    st.success(f"Task '{title}' created successfully!")
                    st.rerun()
                    return True
                    
                st.error("Failed to create task")
                return False
                
            except Exception as e:
                st.error(f"Error creating task: {str(e)}")
                return False
    return False
