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
                    # Get database connection
                    conn = get_connection()
                    if not conn:
                        logger.error("Database connection failed")
                        st.error("Database connection failed. Please try again.")
                        return False
                    
                    # Create cursor
                    cur = conn.cursor()
                    logger.info("Database cursor created")
                    
                    # Debug output
                    st.info("Attempting to create task...")
                    
                    # First verify project exists
                    cur.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
                    project = cur.fetchone()
                    if not project:
                        error_msg = f"Project {project_id} not found"
                        logger.error(error_msg)
                        st.error(error_msg)
                        return False
                    
                    # Log task details before insert
                    st.info(f"Creating task with title: {title}")
                    logger.info(f"Task details - Title: {title}, Status: {status}, Priority: {priority}")
                    
                    # Insert task
                    insert_query = '''
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, assignee, due_date)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    '''
                    
                    values = (project_id, title, description, status, priority, assignee, due_date)
                    logger.info(f"Executing insert with values: {values}")
                    
                    # Show query being executed (for debugging)
                    formatted_query = cur.mogrify(insert_query, values).decode('utf-8')
                    st.code(formatted_query, language='sql')
                    
                    cur.execute(insert_query, values)
                    result = cur.fetchone()
                    
                    if not result:
                        error_msg = "Task insert failed - no ID returned"
                        logger.error(error_msg)
                        st.error(error_msg)
                        raise Exception(error_msg)
                    
                    task_id = result[0]
                    logger.info(f"Task created with ID: {task_id}")
                    st.info(f"Task created with ID: {task_id}")
                    
                    # Verify task exists
                    cur.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
                    verify = cur.fetchone()
                    if not verify:
                        error_msg = f"Task verification failed for ID: {task_id}"
                        logger.error(error_msg)
                        st.error(error_msg)
                        raise Exception(error_msg)
                    
                    # Commit transaction
                    conn.commit()
                    logger.info("Transaction committed successfully")
                    
                    # Show success message with details
                    success_msg = f"Task '{title}' created successfully! (ID: {task_id})"
                    st.success(success_msg)
                    time.sleep(0.5)  # Brief pause
                    st.rerun()
                    return True
                    
                except Exception as e:
                    error_msg = f"Task creation failed: {str(e)}"
                    logger.error(error_msg)
                    if conn:
                        conn.rollback()
                        logger.info("Transaction rolled back")
                    st.error(error_msg)
                    # Show detailed error information
                    st.error("Debug information:")
                    st.code(f"Error type: {type(e).__name__}\nError details: {str(e)}")
                    return False
                finally:
                    if cur:
                        cur.close()
                    if conn:
                        conn.close()
                        logger.info("Database connection closed")
                        
    except Exception as e:
        error_msg = f"Form error: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        return False
