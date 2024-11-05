import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        with st.form("task_form", clear_on_submit=True):
            st.write("### Create Task")
            st.write(f"Debug: Creating task for project {project_id}")
            
            title = st.text_input("Title")
            description = st.text_area("Description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            due_date = st.date_input("Due Date")
            
            uploaded_file = st.file_uploader("Attach File")
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("Title is required")
                    return False
                    
                try:
                    # Debug output
                    st.write("Debug: Creating task with data:")
                    st.json({
                        "project_id": project_id,
                        "title": title,
                        "description": description,
                        "status": status,
                        "priority": priority,
                        "due_date": str(due_date)
                    })
                    
                    # Create task
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status, priority, due_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id, title, status;
                    ''', (project_id, title, description, status, priority, due_date))
                    
                    if result:
                        task_id = result[0]['id']
                        st.success(f"Task '{title}' created successfully!")
                        
                        # Handle file upload if present
                        if uploaded_file:
                            file_id = save_uploaded_file(uploaded_file, task_id)
                            if file_id:
                                st.success(f"File '{uploaded_file.name}' attached successfully!")
                            else:
                                st.warning("Failed to attach file, but task was created")
                        
                        st.experimental_rerun()
                        return True
                    
                    st.error("Failed to create task")
                    return False
                    
                except Exception as e:
                    st.error(f"Error creating task: {str(e)}")
                    logger.error(f"Task creation error: {str(e)}")
                    return False
                    
    except Exception as e:
        st.error(f"Form error: {str(e)}")
        logger.error(f"Form error: {str(e)}")
        return False
