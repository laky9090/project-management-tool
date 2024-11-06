import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging
import os

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project {project_id}")
        with st.form("task_form", clear_on_submit=True):
            st.write("### Create Task")
            
            # Debug info
            st.write(f"Debug: Creating task for project {project_id}")
            
            # Form fields
            title = st.text_input("Title", key=f"task_title_{project_id}")
            description = st.text_area("Description", key=f"task_desc_{project_id}")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"], key=f"task_status_{project_id}")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"], key=f"task_priority_{project_id}")
            due_date = st.date_input("Due Date", key=f"task_due_date_{project_id}")
            
            # File upload field with clear instructions
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
                    # Debug info before insert
                    debug_data = {
                        "project_id": project_id,
                        "title": title,
                        "description": description,
                        "status": status,
                        "priority": priority,
                        "due_date": str(due_date)
                    }
                    logger.info(f"Attempting to create task with data: {debug_data}")
                    st.write("Debug: Creating task with data:")
                    st.json(debug_data)
                    
                    # Begin transaction
                    logger.info("Beginning database transaction")
                    result = execute_query('BEGIN')
                    
                    # Insert task
                    insert_query = '''
                        INSERT INTO tasks (project_id, title, description, status, priority, due_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING *;
                    '''
                    logger.info(f"Executing insert query: {insert_query}")
                    result = execute_query(
                        insert_query,
                        (project_id, title, description, status, priority, due_date)
                    )
                    
                    if result:
                        task_id = result[0]['id']
                        logger.info(f"Task created successfully: {result[0]}")
                        
                        # Handle file upload if present
                        file_id = None
                        if uploaded_file:
                            try:
                                logger.info(f"Attempting to save file: {uploaded_file.name}")
                                os.makedirs('uploads', exist_ok=True)
                                file_id = save_uploaded_file(uploaded_file, task_id)
                                if not file_id:
                                    logger.warning("Failed to save file attachment")
                                    st.warning("Failed to save file attachment, but task was created")
                                else:
                                    logger.info(f"File attachment saved successfully: {file_id}")
                            except Exception as e:
                                logger.error(f"File upload error: {str(e)}")
                                st.warning(f"Failed to upload file: {str(e)}")
                        
                        execute_query('COMMIT')
                        
                        # Verify task was created by querying it back
                        verify_query = "SELECT * FROM tasks WHERE id = %s"
                        verify_result = execute_query(verify_query, (task_id,))
                        if verify_result:
                            logger.info(f"Task verified in database: {verify_result[0]}")
                        else:
                            logger.error("Task created but not found in verification query")
                        
                        success_message = f"Task '{title}' created successfully!"
                        if file_id:
                            success_message += f"\nFile '{uploaded_file.name}' attached."
                        st.success(success_message)
                        st.write("Debug: Created task data:", result[0])
                        
                        # Force refresh
                        st.rerun()
                        return True
                    
                    logger.error("Insert query returned no result")
                    execute_query('ROLLBACK')
                    st.error("Failed to create task - database error")
                    return False
                    
                except Exception as e:
                    logger.error(f"Error creating task: {str(e)}")
                    execute_query('ROLLBACK')
                    st.error(f"Error creating task: {str(e)}")
                    return False
                    
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error(f"Form error: {str(e)}")
        return False
