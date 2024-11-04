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
                    st.error("Task title is required!")
                    return False
                
                conn = None
                cur = None
                try:
                    # Get database connection
                    conn = get_connection()
                    if not conn:
                        logger.error("Failed to establish database connection")
                        st.error("Database connection failed")
                        return False
                    
                    # Create cursor
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    logger.info("Database cursor created")
                    
                    # Start transaction
                    cur.execute("BEGIN")
                    logger.info("Transaction started")
                    
                    # Log task creation attempt
                    logger.info(f"Attempting to create task: Title='{title}', Project={project_id}, Status={status}")
                    
                    # Insert task
                    insert_query = '''
                        INSERT INTO tasks 
                        (project_id, title, description, status, priority, assignee, due_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    '''
                    
                    values = (project_id, title, description, status, priority, assignee, due_date)
                    
                    # Log the exact query being executed
                    logger.info(f"Executing query: {cur.mogrify(insert_query, values).decode('utf-8')}")
                    
                    # Execute insert
                    cur.execute(insert_query, values)
                    result = cur.fetchone()
                    
                    if not result:
                        logger.error("Insert did not return an ID")
                        raise Exception("Task creation failed - no ID returned")
                    
                    task_id = result['id']
                    logger.info(f"Task inserted with ID: {task_id}")
                    
                    # Verify the task exists
                    verify_query = "SELECT * FROM tasks WHERE id = %s"
                    cur.execute(verify_query, (task_id,))
                    verify_result = cur.fetchone()
                    
                    if not verify_result:
                        logger.error(f"Could not verify task {task_id} exists")
                        raise Exception("Task verification failed")
                    
                    logger.info(f"Task verified: {verify_result}")
                    
                    # Commit transaction
                    conn.commit()
                    logger.info("Transaction committed successfully")
                    
                    st.success(f"Task '{title}' created successfully!")
                    time.sleep(0.1)  # Brief pause
                    st.rerun()
                    return True
                    
                except Exception as e:
                    logger.error(f"Error creating task: {str(e)}")
                    if conn:
                        conn.rollback()
                        logger.info("Transaction rolled back")
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
