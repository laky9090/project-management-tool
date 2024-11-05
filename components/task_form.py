import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    with st.form("task_form"):
        st.write("### Create Task")
        
        title = st.text_input("Title", help="Enter the task title")
        description = st.text_area("Description", help="Enter task description")
        
        col1, col2 = st.columns(2)
        with col1:
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        with col2:
            due_date = st.date_input("Due Date", help="Select task due date")
        
        # File upload with better UX
        uploaded_file = st.file_uploader(
            "Attach File",
            type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xlsx', 'csv'],
            help="Supported formats: PDF, Text, Images, Word documents, Excel sheets"
        )
        
        if uploaded_file:
            st.write("File selected:", uploaded_file.name)
            st.write("File size:", f"{uploaded_file.size/1024:.1f} KB")
        
        submitted = st.form_submit_button("Create Task")
        
        if submitted and title:
            try:
                # Insert task
                result = execute_query('''
                    INSERT INTO tasks (project_id, title, description, status, priority, due_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, title, status;
                ''', (project_id, title, description, status, priority, due_date))
                
                if result:
                    task_id = result[0]['id']
                    
                    # Handle file attachment
                    if uploaded_file:
                        with st.spinner('Uploading file...'):
                            attachment_id = save_uploaded_file(uploaded_file, task_id)
                            if attachment_id:
                                st.success(f"✅ Task created and file '{uploaded_file.name}' attached successfully!")
                            else:
                                st.warning("⚠️ Task created but file attachment failed")
                    else:
                        st.success("✅ Task created successfully!")
                    
                    st.rerun()
                    return True
                
                st.error("Failed to create task")
                return False
                
            except Exception as e:
                logger.error(f"Error creating task: {str(e)}")
                st.error(f"Error: {str(e)}")
                return False
    return False
