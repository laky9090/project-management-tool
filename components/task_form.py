import streamlit as st
from database.connection import get_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project {project_id}")
        with st.form("task_form", clear_on_submit=True):  # Add clear_on_submit
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
                    
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    
                    # Start transaction
                    cur.execute("BEGIN")
                    
                    # Insert task with RETURNING clause
                    insert_query = '''
                        INSERT INTO tasks 
                        (project_id, title, description, status, priority, assignee, due_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    '''
                    
                    logger.info(f"Inserting task: {title} for project {project_id}")
                    cur.execute(insert_query, (
                        project_id, title, description, 
                        status, priority, assignee, due_date
                    ))
                    
                    result = cur.fetchone()
                    logger.info(f"Insert result: {result}")
                    
                    if not result:
                        logger.error("Task creation failed - no ID returned")
                        conn.rollback()
                        st.error("Failed to create task")
                        return False
                    
                    # Verify the task exists
                    verify_query = "SELECT id FROM tasks WHERE id = %s"
                    cur.execute(verify_query, (result['id'],))
                    verify_result = cur.fetchone()
                    
                    if not verify_result:
                        logger.error("Task verification failed")
                        conn.rollback()
                        st.error("Failed to verify task creation")
                        return False
                    
                    # If we got here, commit the transaction
                    conn.commit()
                    logger.info(f"Task created successfully with ID: {result['id']}")
                    st.success(f"Task '{title}' created successfully!")
                    time.sleep(0.1)  # Brief pause before refresh
                    st.rerun()
                    return True
                    
                except Exception as e:
                    if conn:
                        conn.rollback()
                    logger.error(f"Task creation error: {str(e)}")
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
        st.error("An error occurred while creating the task")
        return False
