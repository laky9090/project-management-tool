import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        with st.form("task_form"):
            st.write("### Add Task")
            
            # Debug info
            st.write(f"Creating task for project: {project_id}")
            
            # Minimal fields
            title = st.text_input("Title", key=f"title_{project_id}")
            description = st.text_area("Description", key=f"desc_{project_id}")
            
            # Simple file upload
            uploaded_file = st.file_uploader(
                "Attach File (optional)",
                type=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx']
            )
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted and title:
                try:
                    # Show debug info
                    st.write("Creating task with data:")
                    st.json({
                        "project_id": project_id,
                        "title": title,
                        "description": description,
                        "status": "To Do",  # Fixed status for now
                        "has_attachment": uploaded_file is not None
                    })
                    
                    # Insert task
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id, title;
                    ''', (project_id, title, description, "To Do"))
                    
                    if result:
                        task_id = result[0]['id']
                        
                        # Handle file upload if present
                        if uploaded_file:
                            file_id = save_uploaded_file(uploaded_file, task_id)
                            if file_id:
                                st.success(f"✅ File '{uploaded_file.name}' attached!")
                        
                        st.success(f"✅ Task '{title}' created!")
                        st.write("Debug - Created task:", result[0])
                        st.rerun()
                        return True
                    
                    st.error("Failed to create task")
                    return False
                    
                except Exception as e:
                    logger.error(f"Error creating task: {str(e)}")
                    st.error(f"Error: {str(e)}")
                    return False
                    
        return False
        
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error(f"Form error: {str(e)}")
        return False
