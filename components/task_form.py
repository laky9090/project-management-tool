import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging
from utils.file_handler import save_uploaded_file, get_task_attachments, delete_attachment

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project {project_id}")
        
        with st.form("task_form"):
            # Debug container at the top
            debug_container = st.empty()
            
            title = st.text_input("Task Title")
            description = st.text_area("Description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            due_date = st.date_input("Due Date", min_value=datetime.today())
            
            # File upload field
            uploaded_file = st.file_uploader("Attach File", 
                type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx'])
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("Task title is required!")
                    return False
                
                try:
                    # Start transaction
                    execute_query("BEGIN")
                    
                    # Show debug info
                    with debug_container:
                        st.write("### Debug Information")
                        st.json({
                            "project_id": project_id,
                            "title": title,
                            "description": description,
                            "status": status,
                            "priority": priority,
                            "due_date": str(due_date)
                        })
                    
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
                        task_id = result[0]['id']
                        logger.info(f"Created task with ID: {task_id}")
                        
                        # Handle file upload if present
                        if uploaded_file:
                            logger.info(f"Uploading file: {uploaded_file.name}")
                            attachment_id = save_uploaded_file(uploaded_file, task_id)
                            if attachment_id is None:
                                logger.error("Failed to save file attachment")
                                execute_query("ROLLBACK")
                                st.error("Failed to save file attachment")
                                return False
                            logger.info(f"Created attachment with ID: {attachment_id}")
                        
                        # Commit transaction
                        execute_query("COMMIT")
                        st.success(f"Task '{title}' created successfully!")
                        
                        # Force reload
                        st.rerun()
                        return True
                    else:
                        logger.error("Failed to create task - database error")
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
