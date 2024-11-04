import streamlit as st
from database.connection import get_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Starting task creation form for project {project_id}")
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
                
                logger.info(f"Creating task with title: {title}")
                
                try:
                    # Use a single connection for the entire operation
                    conn = get_connection()
                    if not conn:
                        st.error("Could not connect to database")
                        return False

                    with conn:
                        with conn.cursor(cursor_factory=RealDictCursor) as cur:
                            # Insert task
                            insert_query = '''
                                INSERT INTO tasks 
                                (project_id, title, description, status, priority, assignee, due_date)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                RETURNING id, title, status;
                            '''
                            logger.info(f"Executing insert query with project_id={project_id}")
                            cur.execute(insert_query, (
                                project_id, title, description, 
                                status, priority, assignee, due_date
                            ))
                            
                            result = cur.fetchone()
                            logger.info(f"Insert result: {result}")
                            
                            if result:
                                # Verify the task was created
                                verify_query = '''
                                    SELECT id, title, status FROM tasks 
                                    WHERE id = %s AND project_id = %s
                                '''
                                cur.execute(verify_query, (result['id'], project_id))
                                verify_result = cur.fetchone()
                                logger.info(f"Verification result: {verify_result}")
                                
                                st.success(f"Task '{title}' created successfully!")
                                st.rerun()
                                return True
                            
                            st.error("Failed to create task: No result returned")
                            return False
                            
                except Exception as e:
                    logger.error(f"Error creating task: {str(e)}")
                    st.error(f"Failed to create task: {str(e)}")
                    return False
                    
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error("An error occurred while creating the task")
        return False
