import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    """Create a new task with optional file attachment."""
    try:
        # Verify project exists
        project = execute_query("SELECT id FROM projects WHERE id = %s", (project_id,))
        if not project:
            st.error("Invalid project ID")
            return False

        with st.form("task_form", clear_on_submit=True):
            st.write("### Create New Task")
            
            # Basic task information
            title = st.text_input("Title", key="task_title")
            description = st.text_area("Description", key="task_description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"], key="task_status")
            due_date = st.date_input("Due Date", key="task_due_date")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"], key="task_priority")
            
            # File upload
            uploaded_file = st.file_uploader(
                "Attach File",
                type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xlsx', 'csv'],
                help="Supported formats: PDF, Text, Images, Word documents, Excel sheets",
                key="task_file"
            )

            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("Please enter a task title")
                    return False
                
                try:
                    # Start transaction
                    execute_query("BEGIN")
                    
                    # Create task
                    task_result = execute_query("""
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, due_date)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (project_id, title, description, status, priority, due_date))
                    
                    if not task_result:
                        execute_query("ROLLBACK")
                        st.error("Failed to create task")
                        return False
                    
                    task_id = task_result[0]['id']
                    
                    # Handle file attachment if present
                    if uploaded_file:
                        attachment_id = save_uploaded_file(uploaded_file, task_id)
                        if not attachment_id:
                            execute_query("ROLLBACK")
                            st.error("Failed to save file attachment")
                            return False
                    
                    # Commit transaction
                    execute_query("COMMIT")
                    
                    # Success message
                    st.success(f"Task '{title}' created successfully!")
                    if uploaded_file:
                        st.success(f"File '{uploaded_file.name}' attached successfully!")
                    
                    # Clear form
                    st.experimental_rerun()
                    return True
                    
                except Exception as e:
                    execute_query("ROLLBACK")
                    logger.error(f"Error creating task: {str(e)}")
                    st.error("An error occurred while creating the task")
                    return False
                    
    except Exception as e:
        logger.error(f"Task form error: {str(e)}")
        st.error("An error occurred while displaying the task form")
        return False
