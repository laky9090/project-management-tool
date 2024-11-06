import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        with st.form("task_form"):
            st.write("### Create Task")
            st.write(f"Debug: Creating task for project {project_id}")
            
            # Simplified form with essential fields
            title = st.text_input("Title")
            description = st.text_area("Description")
            status = st.selectbox("Status", ["To Do"])
            
            # Add file upload field
            uploaded_file = st.file_uploader(
                "Attach File",
                type=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'],
                help="Upload a file (max 200MB)"
            )
            
            # Debug container
            debug_container = st.empty()
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted and title:
                try:
                    # Show debug info before insert
                    with debug_container:
                        st.write("Debug: Creating task with data:")
                        st.json({
                            "project_id": project_id,
                            "title": title,
                            "description": description,
                            "status": status,
                            "has_attachment": uploaded_file is not None
                        })
                    
                    # Insert task
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status)
                        VALUES (%s, %s, %s, %s)
                        RETURNING *;
                    ''', (project_id, title, description, status))
                    
                    if result:
                        task_id = result[0]['id']
                        
                        # Handle file upload if present
                        if uploaded_file:
                            file_id = save_uploaded_file(uploaded_file, task_id)
                            if file_id:
                                st.success(f"File '{uploaded_file.name}' attached successfully!")
                            else:
                                st.warning("Failed to save file attachment")
                        
                        st.success(f"Task '{title}' created successfully!")
                        st.write("Debug: Created task data:", result[0])
                        
                        # Verify task was created
                        verify = execute_query(
                            "SELECT * FROM tasks WHERE id = %s",
                            (task_id,)
                        )
                        st.write("Debug: Verification query result:", verify)
                        
                        st.rerun()
                        return True
                    
                    st.error("Failed to create task - database error")
                    return False
                    
                except Exception as e:
                    logger.error(f"Error creating task: {str(e)}")
                    st.error(f"Error creating task: {str(e)}")
                    return False
                    
        return False
        
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error(f"Form error: {str(e)}")
        return False
