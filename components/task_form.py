import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project {project_id}")
        
        # Add error message container
        error_container = st.empty()
        debug_container = st.empty()
        
        with st.form("task_form", clear_on_submit=True):
            # Add form fields with current values for debugging
            st.write("### Current Form Values:")
            st.json({
                "project_id": project_id,
                "title": st.session_state.get("task_title", ""),
                "status": st.session_state.get("task_status", "To Do"),
                "priority": st.session_state.get("task_priority", "Medium")
            })
            
            title = st.text_input("Task Title", key="task_title")
            description = st.text_area("Description", key="task_description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"], key="task_status")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"], key="task_priority")
            assignee = st.text_input("Assignee", key="task_assignee")
            due_date = st.date_input("Due Date", min_value=datetime.today(), key="task_due_date")
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    error_container.error("⚠️ Task title is required!")
                    return False
                
                try:
                    # Show debug information
                    debug_container.info("📝 Creating task...")
                    debug_container.write("Form values:")
                    debug_container.json({
                        "project_id": project_id,
                        "title": title,
                        "description": description,
                        "status": status,
                        "priority": priority,
                        "assignee": assignee,
                        "due_date": due_date
                    })
                    
                    # First verify project exists
                    project = execute_query(
                        "SELECT id FROM projects WHERE id = %s FOR UPDATE",
                        (project_id,)
                    )
                    if not project:
                        error_container.error(f"⚠️ Project {project_id} not found")
                        return False
                    
                    debug_container.info(f"Creating task '{title}' for project {project_id}...")
                    
                    # Insert task
                    insert_query = '''
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, assignee, due_date)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, title, status;
                    '''
                    
                    values = (project_id, title, description, status, priority, assignee, due_date)
                    
                    # Show query information
                    debug_container.code("SQL Query:", language="sql")
                    debug_container.code(insert_query)
                    debug_container.write("Values:")
                    debug_container.json(values)
                    
                    result = execute_query(insert_query, values)
                    debug_container.info(f"Query result: {result}")
                    
                    if not result:
                        error_container.error("⚠️ Task creation failed - no ID returned")
                        debug_container.error("Database error - no result returned")
                        return False
                    
                    # Verify task exists
                    debug_container.info("Verifying task creation...")
                    verify_result = execute_query(
                        "SELECT * FROM tasks WHERE id = %s AND project_id = %s",
                        (result[0]['id'], project_id)
                    )
                    
                    if not verify_result:
                        error_container.error("⚠️ Task verification failed")
                        debug_container.error("Task not found after creation")
                        return False
                    
                    st.success(f"✅ Task '{title}' created successfully!")
                    debug_container.success(f"Task created with ID: {result[0]['id']}")
                    
                    time.sleep(1)  # Give user time to see the success message
                    st.rerun()
                    return True
                    
                except Exception as e:
                    error_container.error(f"⚠️ Error: {str(e)}")
                    debug_container.error("Debug information:")
                    debug_container.code(f"Error type: {type(e).__name__}")
                    debug_container.code(f"Error details: {str(e)}")
                    logger.error(f"Task creation failed: {str(e)}")
                    return False
                    
    except Exception as e:
        st.error(f"Form error: {str(e)}")
        logger.error(f"Form error: {str(e)}")
        return False
