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
            status = st.selectbox("Status", ["To Do"])
            
            # File upload with validation
            uploaded_file = st.file_uploader(
                "Attach File",
                type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xlsx', 'csv'],
                help="Supported formats: PDF, Text, Images, Word documents, Excel sheets"
            )

            # Debug container before submit
            debug_container = st.empty()
            
            # Show file details if uploaded
            if uploaded_file:
                st.write("Debug: File details:", {
                    "filename": uploaded_file.name,
                    "type": uploaded_file.type,
                    "size": f"{uploaded_file.size/1024:.1f} KB"
                })
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted and title:
                # Show debug info before insert
                with debug_container:
                    st.write("### Debug: Task Data")
                    st.json({
                        "project_id": project_id,
                        "title": title,
                        "description": description,
                        "status": status,
                        "has_attachment": uploaded_file is not None
                    })
                
                # Insert with explicit error handling
                try:
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status) 
                        VALUES (%s, %s, %s, %s) 
                        RETURNING id, title, status;
                    ''', (project_id, title, description, status))
                    
                    if result:
                        task_id = result[0]['id']
                        logger.info(f"Task created successfully with ID: {task_id}")
                        
                        # Handle file attachment if present
                        if uploaded_file:
                            st.write("Debug: Processing file attachment...")
                            attachment_id = save_uploaded_file(uploaded_file, task_id)
                            
                            if attachment_id:
                                st.success(f"✅ Task created and file '{uploaded_file.name}' attached successfully!")
                                st.write("Debug: Attachment created with ID:", attachment_id)
                            else:
                                st.warning(f"⚠️ Task created but file attachment failed")
                                logger.error("File attachment failed - no attachment ID returned")
                        else:
                            st.success("✅ Task created successfully!")
                        
                        st.write("Debug: Created task data:", result[0])
                        st.experimental_rerun()
                        return True
                    
                    st.error("Failed to create task - no result returned")
                    logger.error("Task creation failed - database insert returned no result")
                    return False
                    
                except Exception as e:
                    logger.error(f"Database error: {str(e)}")
                    st.error(f"Database error: {str(e)}")
                    return False
            
            elif submitted:
                st.error("Please enter a title for the task")
                
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error(f"Form error: {str(e)}")
        return False
    return False
