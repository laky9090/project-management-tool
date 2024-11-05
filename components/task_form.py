import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    with st.form("task_form"):
        st.write("### Create Task")
        
        # Debug container
        debug_container = st.empty()
        
        title = st.text_input("Title")
        description = st.text_area("Description")
        status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
        
        # Add file upload field
        uploaded_file = st.file_uploader("Attach File", type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx'])
        
        submitted = st.form_submit_button("Create Task")
        
        if submitted and title:
            try:
                # Show debug info
                with debug_container:
                    st.write("### Debug Information")
                    st.write(f"Creating task for project {project_id}")
                    st.json({
                        "title": title,
                        "description": description,
                        "status": status,
                        "has_attachment": uploaded_file is not None
                    })
                
                # Create task
                result = execute_query('''
                    INSERT INTO tasks (project_id, title, description, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, title;
                ''', (project_id, title, description, status))
                
                if result:
                    task_id = result[0]['id']
                    
                    # Handle file upload if present
                    if uploaded_file:
                        attachment_id = save_uploaded_file(uploaded_file, task_id)
                        if attachment_id:
                            st.success(f"File '{uploaded_file.name}' attached successfully")
                        else:
                            st.warning("Failed to save file attachment")
                    
                    st.success(f"Task '{title}' created successfully!")
                    st.write("Created task:", result[0])
                    st.rerun()
                    return True
                
                st.error("Failed to create task")
                return False
                
            except Exception as e:
                logger.error(f"Error creating task: {str(e)}")
                st.error(f"Error: {str(e)}")
                return False
    return False
