import streamlit as st
from database.connection import get_connection
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
                    
                conn = None
                cur = None
                try:
                    conn = get_connection()
                    if not conn:
                        st.error("Database connection failed")
                        return False
                        
                    cur = conn.cursor()
                    
                    # First verify project exists
                    cur.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
                    if not cur.fetchone():
                        st.error(f"Project {project_id} not found")
                        return False
                    
                    # Insert task with explicit column names
                    insert_query = '''
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, assignee, due_date, created_at)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        RETURNING id
                    '''
                    
                    values = (project_id, title, description, status, priority, assignee, due_date)
                    logger.info(f"Executing insert with values: {values}")
                    
                    cur.execute(insert_query, values)
                    result = cur.fetchone()
                    
                    if not result:
                        raise Exception("Task creation failed - no ID returned")
                    
                    task_id = result[0]
                    logger.info(f"Task created with ID: {task_id}")
                    
                    # Verify task exists
                    cur.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
                    if not cur.fetchone():
                        raise Exception("Task verification failed")
                    
                    conn.commit()
                    logger.info(f"Transaction committed successfully")
                    
                    st.success(f"Task '{title}' created successfully!")
                    st.session_state.clear()  # Clear form state
                    st.rerun()
                    return True
                    
                except Exception as e:
                    if conn:
                        conn.rollback()
                    logger.error(f"Task creation failed: {str(e)}")
                    st.error(f"Failed to create task: {str(e)}")
                    return False
                finally:
                    if cur:
                        cur.close()
                    if conn:
                        conn.close()
                        logger.info("Database connection closed")
                        
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        return False
