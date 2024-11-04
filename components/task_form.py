import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project {project_id}")
        with st.form("task_form", clear_on_submit=True):
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
                    # First verify project exists
                    st.info("Verifying project...")
                    project = execute_query("SELECT id FROM projects WHERE id = %s", (project_id,))
                    if not project:
                        st.error(f"Project {project_id} not found")
                        return False
                    
                    st.info(f"Creating task '{title}' for project {project_id}...")
                    
                    # Insert task using execute_query
                    insert_query = '''
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, assignee, due_date)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, title, status;
                    '''
                    
                    values = (project_id, title, description, status, priority, assignee, due_date)
                    st.code(f"Executing query with values: {values}", language='python')
                    
                    result = execute_query(insert_query, values)
                    st.info(f"Insert query result: {result}")
                    
                    if not result:
                        st.error("Task creation failed - no ID returned")
                        return False
                    
                    # Verify task exists
                    verify_result = execute_query(
                        "SELECT id, title FROM tasks WHERE id = %s",
                        (result[0]['id'],)
                    )
                    
                    if not verify_result:
                        st.error("Task verification failed")
                        return False
                    
                    st.success(f"Task '{title}' created successfully!")
                    time.sleep(0.5)  # Brief pause before refresh
                    st.rerun()
                    return True
                    
                except Exception as e:
                    st.error(f"Error creating task: {str(e)}")
                    st.error("Debug information:")
                    st.code(f"Error type: {type(e).__name__}\nError details: {str(e)}")
                    return False
                    
    except Exception as e:
        st.error(f"Form error: {str(e)}")
        return False
