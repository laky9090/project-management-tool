import streamlit as st
from database.connection import get_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

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
                    # Use with statement for automatic connection handling
                    with get_connection() as conn:
                        with conn.cursor(cursor_factory=RealDictCursor) as cur:
                            # Start transaction
                            cur.execute("BEGIN")
                            
                            # Insert task
                            insert_query = '''
                                INSERT INTO tasks 
                                (project_id, title, description, status, priority, assignee, due_date)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                RETURNING id, title, status;
                            '''
                            
                            logger.info(f"Creating task with data: project_id={project_id}, title={title}")
                            cur.execute(insert_query, (
                                project_id, title, description, 
                                status, priority, assignee, due_date
                            ))
                            
                            result = cur.fetchone()
                            logger.info(f"Insert result: {result}")
                            
                            if not result:
                                raise Exception("Task creation failed - no ID returned")
                            
                            # Commit transaction
                            conn.commit()
                            logger.info(f"Task created successfully with ID: {result['id']}")
                            
                            # Show success message
                            st.success(f"Task '{title}' created successfully!")
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
