import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    with st.form("task_form"):
        st.write("### Create Task")
        st.write(f"Debug: Creating task for project {project_id}")
        
        title = st.text_input("Title")
        description = st.text_area("Description")
        status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
        
        # Add file upload field
        uploaded_file = st.file_uploader("Attach File", type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx'])
        
        submitted = st.form_submit_button("Create Task")
        
        if submitted and title:
            try:
                # Debug: Show what we're about to insert
                st.write("### Debug Information")
                st.write("Inserting task with data:")
                st.json({
                    "project_id": project_id,
                    "title": title,
                    "description": description,
                    "status": status,
                    "has_attachment": uploaded_file is not None
                })
                
                # Start transaction
                execute_query('BEGIN')
                
                # Insert task
                result = execute_query('''
                    INSERT INTO tasks (project_id, title, description, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *;
                ''', (project_id, title, description, status))
                
                if result:
                    task_id = result[0]['id']
                    # Show created task
                    st.write("Debug: Created task data:")
                    st.json(dict(result[0]))
                    
                    # Handle file upload if present
                    if uploaded_file:
                        attachment_id = save_uploaded_file(uploaded_file, task_id)
                        if attachment_id:
                            st.success(f"File '{uploaded_file.name}' attached successfully")
                            st.write("Debug: Created attachment with ID:", attachment_id)
                        else:
                            execute_query('ROLLBACK')
                            st.error("Failed to save file attachment")
                            return False
                    
                    # Commit transaction
                    execute_query('COMMIT')
                    st.success(f"Task '{title}' created successfully!")
                    st.rerun()
                    return True
                
                # Rollback if no result
                execute_query('ROLLBACK')
                st.error("Failed to create task - no result returned")
                return False
                
            except Exception as e:
                # Rollback on error
                execute_query('ROLLBACK')
                logger.error(f"Error creating task: {str(e)}")
                st.error(f"Error creating task: {str(e)}")
                return False
    return False
