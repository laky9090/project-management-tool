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
        status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
        
        # Add file upload field
        uploaded_file = st.file_uploader("Attach File", type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx'])
        
        submitted = st.form_submit_button("Create Task")
        
        if submitted and title:
            try:
                # Debug info
                st.write("### Debug: Creating task")
                st.write(f"Project ID: {project_id}")
                st.write(f"Title: {title}")
                st.write(f"Status: {status}")
                st.write(f"Has attachment: {uploaded_file is not None}")
                
                # Simple insert
                result = execute_query(
                    'INSERT INTO tasks (project_id, title, status) VALUES (%s, %s, %s) RETURNING id, title;',
                    (project_id, title, status)
                )
                
                if result:
                    task_id = result[0]['id']
                    st.success(f"Task created with ID: {task_id}")
                    st.write("Debug: Created task:", result[0])
                    
                    # Handle file upload if present
                    if uploaded_file:
                        attachment_id = save_uploaded_file(uploaded_file, task_id)
                        if attachment_id:
                            st.success(f"File '{uploaded_file.name}' attached successfully")
                            st.write("Debug: Created attachment with ID:", attachment_id)
                        else:
                            st.warning("Failed to save file attachment")
                    
                    # Query to verify task exists
                    verify = execute_query(
                        'SELECT * FROM tasks WHERE id = %s',
                        (task_id,)
                    )
                    st.write("Debug: Verification query result:", verify[0] if verify else None)
                    st.rerun()
                    return True
                
                st.error("Failed to create task")
                return False
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                return False
    return False
