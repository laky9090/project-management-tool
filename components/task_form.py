import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project_id: {project_id}")
        with st.form("task_form"):
            st.write("Create New Task")
            title = st.text_input("Task Title", key="task_title")
            description = st.text_area("Description", key="task_description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"], key="task_status")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"], key="task_priority")
            assignee = st.text_input("Assignee", key="task_assignee")
            due_date = st.date_input("Due Date", min_value=datetime.today(), key="task_due_date")
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("Task title is required!")
                    return False
                
                try:
                    logger.info(f"Creating task: {title} for project {project_id}")
                    result = execute_query('''
                        INSERT INTO tasks 
                        (project_id, title, description, status, priority, assignee, due_date)
                        VALUES 
                        (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (project_id, title, description, status, priority, assignee, due_date))
                    
                    if result and len(result) > 0:
                        task_id = result[0]['id']
                        logger.info(f"Task created successfully with ID: {task_id}")
                        st.success("Task created successfully!")
                        # Clear form fields by triggering a rerun
                        st.rerun()
                        return True
                    else:
                        logger.error("Task creation failed: No ID returned")
                        st.error("Failed to create task. Please try again.")
                        return False
                        
                except Exception as e:
                    logger.error(f"Task creation failed: {str(e)}")
                    st.error(f"Failed to create task: {str(e)}")
                    return False
    except Exception as e:
        logger.error(f"Error in create_task_form: {str(e)}")
        st.error("An error occurred while creating the task")
        return False
