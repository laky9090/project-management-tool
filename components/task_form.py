import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project {project_id}")
        
        with st.form("task_form"):
            title = st.text_input("Task Title")
            description = st.text_area("Description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            due_date = st.date_input("Due Date", min_value=datetime.today())
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("Task title is required!")
                    return False
                
                try:
                    # Start transaction
                    execute_query("BEGIN")
                    
                    # Insert task
                    insert_query = '''
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, due_date)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    '''
                    
                    values = (
                        project_id,
                        title,
                        description,
                        status,
                        priority,
                        due_date
                    )
                    
                    result = execute_query(insert_query, values)
                    
                    if result:
                        # Commit transaction
                        execute_query("COMMIT")
                        task_id = result[0]['id']
                        st.success(f"Task '{title}' created successfully! (ID: {task_id})")
                        
                        # Update session state to trigger rerun on next render
                        if 'task_created' not in st.session_state:
                            st.session_state.task_created = []
                        st.session_state.task_created.append(task_id)
                        
                        return True
                    else:
                        execute_query("ROLLBACK")
                        st.error("Failed to create task - database error")
                        return False
                        
                except Exception as e:
                    execute_query("ROLLBACK")
                    st.error(f"Error creating task: {str(e)}")
                    logger.error(f"Task creation error: {str(e)}")
                    return False
                    
    except Exception as e:
        st.error(f"Form error: {str(e)}")
        logger.error(f"Form error: {str(e)}")
        return False
