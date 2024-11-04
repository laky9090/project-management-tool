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
                    conn = get_connection()
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    
                    # Start transaction
                    cur.execute("BEGIN")
                    logger.info("Transaction started")
                    
                    # First verify project exists
                    cur.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
                    if not cur.fetchone():
                        raise Exception(f"Project {project_id} not found")
                    
                    # Insert task
                    insert_query = '''
                        INSERT INTO tasks 
                        (project_id, title, description, status, priority, assignee, due_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, title, status;
                    '''
                    
                    values = (project_id, title, description, status, priority, assignee, due_date)
                    logger.info(f"Inserting task with values: {values}")
                    
                    cur.execute(insert_query, values)
                    result = cur.fetchone()
                    logger.info(f"Insert result: {result}")
                    
                    if not result:
                        raise Exception("Task creation failed - no ID returned")
                    
                    # Verify task was created
                    cur.execute('''
                        SELECT id, title, status FROM tasks 
                        WHERE id = %s
                    ''', (result['id'],))
                    
                    verify_result = cur.fetchone()
                    logger.info(f"Verification result: {verify_result}")
                    
                    if not verify_result:
                        raise Exception("Task verification failed")
                    
                    # Commit transaction
                    conn.commit()
                    logger.info(f"Transaction committed. Task created with ID: {result['id']}")
                    
                    st.success(f"Task '{title}' created successfully!")
                    time.sleep(0.5)  # Brief pause before refresh
                    st.rerun()
                    return True
                    
                except Exception as e:
                    if conn:
                        conn.rollback()
                        logger.error(f"Transaction rolled back: {str(e)}")
                    raise
                finally:
                    if cur:
                        cur.close()
                    if conn:
                        conn.close()
                        logger.info("Database connection closed")
                        
    except Exception as e:
        logger.error(f"Task creation error: {str(e)}")
        st.error(f"Failed to create task: {str(e)}")
        return False
