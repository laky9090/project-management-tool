import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        with st.form("task_form", clear_on_submit=True):
            st.write("### Create Task")
            
            # Debug container at the top
            debug_container = st.empty()
            
            title = st.text_input("Title")
            description = st.text_area("Description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            
            # Add file upload field
            uploaded_file = st.file_uploader("Attach File", type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx'])
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted and title:
                try:
                    # Show debug info before insert
                    with debug_container:
                        st.write("### Debug Information")
                        st.json({
                            "project_id": project_id,
                            "title": title,
                            "description": description,
                            "status": status,
                            "has_attachment": uploaded_file is not None
                        })
                    
                    # Start transaction for task creation and file upload
                    execute_query("BEGIN")
                    
                    # Create task
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id, title
                    ''', (project_id, title, description, status))
                    
                    if result:
                        task_id = result[0]['id']
                        
                        # Handle file upload if present
                        if uploaded_file:
                            logger.info(f"Saving attachment for task {task_id}")
                            attachment_id = save_uploaded_file(uploaded_file, task_id)
                            if attachment_id is None:
                                execute_query("ROLLBACK")
                                st.error("Failed to save file attachment")
                                return False
                        
                        execute_query("COMMIT")
                        st.success(f"Task '{title}' created successfully!")
                        st.rerun()
                        return True
                    
                    execute_query("ROLLBACK")
                    st.error("Failed to create task")
                    return False
                    
                except Exception as e:
                    execute_query("ROLLBACK")
                    logger.error(f"Error creating task: {str(e)}")
                    st.error(f"Error creating task: {str(e)}")
                    return False
        return False
    except Exception as e:
        logger.error(f"Task form error: {str(e)}")
        st.error(f"Task form error: {str(e)}")
        return False
