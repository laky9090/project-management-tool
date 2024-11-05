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
            
            # Form fields
            title = st.text_input("Title")
            description = st.text_area("Description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            
            # File upload with validation
            uploaded_file = st.file_uploader(
                "Attach File",
                type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xlsx', 'csv'],
                help="Supported formats: PDF, Text, Images, Word documents, Excel sheets"
            )
            
            if uploaded_file:
                st.write("Debug: File details:")
                st.json({
                    "filename": uploaded_file.name,
                    "type": uploaded_file.type,
                    "size": f"{uploaded_file.size/1024:.1f} KB"
                })
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted and title:
                # Show what we're about to insert
                st.write("Debug: About to insert task with data:")
                st.json({
                    "project_id": project_id,
                    "title": title,
                    "description": description,
                    "status": status,
                    "has_attachment": uploaded_file is not None
                })
                
                # Insert task with explicit column names
                result = execute_query('''
                    INSERT INTO tasks 
                        (project_id, title, description, status)
                    VALUES 
                        (%s, %s, %s, %s)
                    RETURNING id, title, status;
                ''', (project_id, title, description, status))
                
                if result:
                    task_id = result[0]['id']
                    st.write("Debug: Created task data:", result[0])
                    
                    # Handle file attachment if present
                    if uploaded_file:
                        try:
                            st.write("Debug: Processing file attachment...")
                            attachment_id = save_uploaded_file(uploaded_file, task_id)
                            
                            if attachment_id:
                                st.success(f"✅ Task created and file '{uploaded_file.name}' attached successfully!")
                                st.write("Debug: Attachment created with ID:", attachment_id)
                            else:
                                st.warning("⚠️ Task created but file attachment failed")
                                logger.error("File attachment failed - no attachment ID returned")
                        except Exception as e:
                            st.warning("⚠️ Task created but file attachment failed")
                            logger.error(f"File attachment error: {str(e)}")
                    else:
                        st.success("✅ Task created successfully!")
                    
                    st.rerun()
                    return True
                
                st.error("Failed to create task - no result returned")
                logger.error("Task creation failed - database insert returned no result")
                return False
                
    except Exception as e:
        error_msg = f"Error creating task: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        return False
    return False
