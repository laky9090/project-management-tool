import streamlit as st
from database.connection import get_connection
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    with st.form("task_form"):
        st.write("Create New Task")
        title = st.text_input("Task Title")
        description = st.text_area("Description")
        status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        assignee = st.text_input("Assignee")
        due_date = st.date_input("Due Date", min_value=datetime.today())
        
        submitted = st.form_submit_button("Create Task")
        
        if submitted:
            if not title:
                st.error("Task title is required!")
                return False
                
            conn = None
            cur = None
            try:
                logger.info(f"Attempting to create task with data: project_id={project_id}, title={title}, status={status}")
                
                conn = get_connection()
                cur = conn.cursor(cursor_factory=RealDictCursor)
                
                # Start transaction
                cur.execute("BEGIN")
                
                # Insert task
                cur.execute('''
                    INSERT INTO tasks 
                    (project_id, title, description, status, priority, assignee, due_date)
                    VALUES 
                    (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (project_id, title, description, status, priority, assignee, due_date))
                
                # Commit transaction
                conn.commit()
                
                task_id = cur.fetchone()['id']
                logger.info(f"Task created successfully with ID: {task_id}, project_id: {project_id}")
                
                st.success("Task created successfully!")
                return True
                
            except Exception as e:
                if conn:
                    conn.rollback()
                logger.error(f"Failed to create task: {str(e)}")
                st.error(f"Error creating task: {str(e)}")
                return False
            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.close()
    return False
