import streamlit as st
from database.connection import execute_query, get_connection
from datetime import datetime
import logging
import time
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project {project_id}")
        
        # Add error message container at the top
        error_placeholder = st.empty()
        debug_placeholder = st.empty()
        
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
                
                conn = None
                cur = None
                try:
                    # Get database connection
                    conn = get_connection()
                    if not conn:
                        error_msg = "Database connection failed"
                        logger.error(error_msg)
                        error_placeholder.error(f"⚠️ {error_msg}")
                        return False
                    
                    # Create cursor
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    
                    # Start transaction
                    cur.execute("BEGIN")
                    debug_placeholder.info("Transaction started...")
                    
                    # Insert task
                    insert_query = '''
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, assignee, due_date)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, title;
                    '''
                    
                    values = (project_id, title, description, status, priority, assignee, due_date)
                    
                    # Log the exact query being executed
                    formatted_query = cur.mogrify(insert_query, values).decode('utf-8')
                    logger.info(f"Executing query: {formatted_query}")
                    debug_placeholder.code(f"Executing query: {formatted_query}")
                    
                    cur.execute(insert_query, values)
                    result = cur.fetchone()
                    
                    if not result:
                        error_msg = "Task creation failed - no ID returned"
                        logger.error(error_msg)
                        error_placeholder.error(f"⚠️ {error_msg}")
                        conn.rollback()
                        debug_placeholder.warning("Transaction rolled back")
                        return False
                    
                    # Verify task exists
                    cur.execute("SELECT * FROM tasks WHERE id = %s", (result['id'],))
                    verify = cur.fetchone()
                    if not verify:
                        error_msg = "Task verification failed"
                        logger.error(error_msg)
                        error_placeholder.error(f"⚠️ {error_msg}")
                        conn.rollback()
                        debug_placeholder.warning("Transaction rolled back")
                        return False
                    
                    # Commit transaction
                    conn.commit()
                    debug_placeholder.success("Transaction committed successfully")
                    
                    success_msg = f"✅ Task '{title}' created successfully! (ID: {result['id']})"
                    st.success(success_msg)
                    logger.info(success_msg)
                    
                    time.sleep(0.5)
                    st.rerun()
                    return True
                    
                except Exception as e:
                    error_msg = f"Error creating task: {str(e)}"
                    logger.error(error_msg)
                    if conn:
                        conn.rollback()
                        debug_placeholder.warning("Transaction rolled back due to error")
                    error_placeholder.error(f"⚠️ {error_msg}")
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
        st.error(f"⚠️ {error_msg}")
        return False
