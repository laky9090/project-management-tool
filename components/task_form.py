import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project {project_id}")
        with st.form("task_form", clear_on_submit=True):
            st.write("### Create Task")
            st.write(f"Creating task for project {project_id}")
            
            # Form fields
            title = st.text_input("Title", key=f"task_title_{project_id}")
            description = st.text_area("Description", key=f"task_desc_{project_id}")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"], key=f"task_status_{project_id}")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"], key=f"task_priority_{project_id}")
            due_date = st.date_input("Due Date", key=f"task_due_date_{project_id}")
            
            uploaded_file = st.file_uploader(
                "Attach File",
                type=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'],
                help="Upload a file (max 200MB)",
                key=f"task_file_{project_id}"
            )
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("Title is required")
                    return False
                    
                try:
                    # Show debug info
                    st.write("Debug: Creating task with data:")
                    task_data = {
                        "project_id": project_id,
                        "title": title,
                        "description": description,
                        "status": status,
                        "priority": priority,
                        "due_date": str(due_date)
                    }
                    st.json(task_data)
                    logger.info(f"Creating task: {task_data}")
                    
                    # Insert task with transaction
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status, priority, due_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id, title, status;
                    ''', (project_id, title, description, status, priority, due_date))
                    
                    if result:
                        task_id = result[0]['id']
                        logger.info(f"Task created with ID: {task_id}")
                        
                        # Handle file upload
                        if uploaded_file:
                            file_id = save_uploaded_file(uploaded_file, task_id)
                            if file_id:
                                logger.info(f"File attachment saved: {file_id}")
                                st.success(f"File '{uploaded_file.name}' attached successfully!")
                            else:
                                logger.warning("Failed to save file attachment")
                                st.warning("Failed to save file attachment")
                        
                        st.success(f"Task '{title}' created successfully!")
                        
                        # Verify task was created
                        verify = execute_query(
                            "SELECT * FROM tasks WHERE id = %s",
                            (task_id,)
                        )
                        if verify:
                            logger.info(f"Task verification successful: {verify[0]}")
                        else:
                            logger.error("Task verification failed")
                        
                        st.rerun()
                        return True
                        
                    logger.error("Task creation failed - no result returned")
                    st.error("Failed to create task")
                    return False
                    
                except Exception as e:
                    logger.error(f"Error creating task: {str(e)}")
                    st.error(f"Error creating task: {str(e)}")
                    return False
                    
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error(f"Form error: {str(e)}")
        return False
