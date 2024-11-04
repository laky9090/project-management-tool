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
                    
                    # Use RealDictCursor for consistency with other queries
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    
                    # Log database connection state
                    st.info("Database connection established...")
                    
                    # Start transaction
                    cur.execute("BEGIN")
                    st.info("Starting database transaction...")
                    
                    # First verify project exists
                    cur.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
                    project = cur.fetchone()
                    if not project:
                        st.error(f"Project {project_id} not found")
                        return False
                    
                    st.info(f"Creating task '{title}' for project {project_id}...")
                    
                    # Insert task with explicit transaction
                    insert_query = '''
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, assignee, due_date)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, title, status;
                    '''
                    
                    values = (project_id, title, description, status, priority, assignee, due_date)
                    
                    # Show the actual query being executed
                    formatted_query = cur.mogrify(insert_query, values).decode('utf-8')
                    st.code(formatted_query, language='sql')
                    
                    # Execute insert
                    cur.execute(insert_query, values)
                    st.info("Executing insert query...")
                    
                    result = cur.fetchone()
                    st.info(f"Insert query result: {result}")
                    
                    if not result:
                        st.error("Task creation failed - no ID returned")
                        conn.rollback()
                        return False
                    
                    # Verify task exists
                    verify_query = '''
                        SELECT id, title, status FROM tasks 
                        WHERE id = %s AND project_id = %s
                    '''
                    cur.execute(verify_query, (result['id'], project_id))
                    verify_result = cur.fetchone()
                    
                    if not verify_result:
                        st.error("Task verification failed")
                        conn.rollback()
                        return False
                    
                    # Commit transaction
                    conn.commit()
                    st.success(f"Task '{title}' created successfully! (ID: {result['id']})")
                    st.info("Transaction committed.")
                    
                    # Brief pause before refresh
                    time.sleep(0.5)
                    st.rerun()
                    return True
                    
                except Exception as e:
                    if conn:
                        conn.rollback()
                    st.error(f"Error creating task: {str(e)}")
                    st.error("Debug information:")
                    st.code(f"Error type: {type(e).__name__}\nError details: {str(e)}")
                    return False
                    
                finally:
                    if cur:
                        cur.close()
                    if conn:
                        conn.close()
                        st.info("Database connection closed")
                        
    except Exception as e:
        st.error(f"Form error: {str(e)}")
        return False
