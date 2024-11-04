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
                
                try:
                    conn = get_connection()
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        # Start transaction
                        cur.execute("BEGIN")
                        
                        # Insert task
                        insert_query = '''
                            INSERT INTO tasks 
                            (project_id, title, description, status, priority, assignee, due_date)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        '''
                        
                        values = (project_id, title, description, status, priority, assignee, due_date)
                        logger.info(f"Executing insert with values: {values}")
                        
                        cur.execute(insert_query, values)
                        result = cur.fetchone()
                        
                        if not result:
                            conn.rollback()
                            st.error("Task creation failed")
                            return False
                            
                        task_id = result['id']
                        
                        # Verify task was created
                        cur.execute('''
                            SELECT id, title, status FROM tasks 
                            WHERE id = %s AND project_id = %s
                        ''', (task_id, project_id))
                        
                        verify_result = cur.fetchone()
                        if not verify_result:
                            conn.rollback()
                            st.error("Task verification failed")
                            return False
                            
                        conn.commit()
                        logger.info(f"Task created and verified with ID: {task_id}")
                        st.success(f"Task '{title}' created successfully!")
                        time.sleep(0.5)  # Brief pause before refresh
                        st.rerun()
                        return True
                        
                except Exception as e:
                    logger.error(f"Task creation error: {str(e)}")
                    st.error(f"Failed to create task: {str(e)}")
                    return False
                    
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error("An error occurred while creating the task")
        return False
