import streamlit as st
from database.connection import get_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    conn = None
    cur = None
    try:
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
                    conn = get_connection()
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    
                    # Begin transaction
                    cur.execute("BEGIN")
                    logger.info(f"Starting transaction for task creation: project_id={project_id}, title={title}")
                    
                    # Insert task
                    cur.execute('''
                        INSERT INTO tasks 
                        (project_id, title, description, status, priority, assignee, due_date)
                        VALUES 
                        (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, title, status
                    ''', (project_id, title, description, status, priority, assignee, due_date))
                    
                    # Fetch and log the result
                    result = cur.fetchone()
                    if result:
                        logger.info(f"Task created successfully: {result}")
                        conn.commit()
                        logger.info("Transaction committed")
                        st.success(f"Task '{title}' created successfully!")
                        st.rerun()
                        return True
                    else:
                        logger.error("No result returned from INSERT")
                        conn.rollback()
                        st.error("Failed to create task: No result returned")
                        return False
                        
                except Exception as e:
                    logger.error(f"Error creating task: {str(e)}")
                    if conn:
                        conn.rollback()
                        logger.info("Transaction rolled back due to error")
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
