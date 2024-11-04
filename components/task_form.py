import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project {project_id}")
        
        # Add error message container at the top
        error_placeholder = st.empty()
        
        with st.form("task_form"):
            title = st.text_input("Task Title", key="task_title")
            description = st.text_area("Description", key="task_description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"], key="task_status")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"], key="task_priority")
            assignee = st.text_input("Assignee", key="task_assignee")
            due_date = st.date_input("Due Date", min_value=datetime.today(), key="task_due_date")
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    error_placeholder.error("⚠️ Task title is required!")
                    return False
                
                try:
                    # Log the attempt
                    logger.info(f"Attempting to create task: {title} for project {project_id}")
                    
                    # Create task with a simple insert
                    insert_query = '''
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, assignee, due_date)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    '''
                    
                    values = (project_id, title, description, status, priority, assignee, due_date)
                    
                    # Show the exact query being executed
                    logger.info(f"Executing query: {insert_query}")
                    logger.info(f"With values: {values}")
                    
                    result = execute_query(insert_query, values)
                    
                    if not result:
                        error_msg = "Task creation failed - database error"
                        logger.error(error_msg)
                        error_placeholder.error(f"⚠️ {error_msg}")
                        return False
                    
                    task_id = result[0]['id']
                    success_msg = f"✅ Task '{title}' created successfully! (ID: {task_id})"
                    st.success(success_msg)
                    logger.info(success_msg)
                    
                    time.sleep(0.5)
                    st.rerun()
                    return True
                    
                except Exception as e:
                    error_msg = f"Error creating task: {str(e)}"
                    logger.error(error_msg)
                    error_placeholder.error(f"⚠️ {error_msg}")
                    return False
                    
    except Exception as e:
        error_msg = f"Form error: {str(e)}"
        logger.error(error_msg)
        st.error(f"⚠️ {error_msg}")
        return False
