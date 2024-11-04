import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project {project_id}")
        
        # Show debug container
        debug_container = st.container()
        with debug_container:
            st.write("### Debug Information")
            st.write("Current project ID:", project_id)
        
        with st.form("task_form"):
            title = st.text_input("Task Title", key="task_title")
            description = st.text_area("Description", key="task_description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"], key="task_status")
            priority = st.selectbox("Priority", ["Low", "Medium", "High"], key="task_priority")
            assignee = st.text_input("Assignee", key="task_assignee")
            due_date = st.date_input("Due Date", min_value=datetime.today(), key="task_due_date")
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("⚠️ Task title is required!")
                    return False
                
                try:
                    # First verify project exists
                    project = execute_query(
                        "SELECT id FROM projects WHERE id = %s",
                        (project_id,)
                    )
                    if not project:
                        st.error(f"Project {project_id} not found!")
                        return False
                    
                    # Show the values being inserted
                    with debug_container:
                        st.write("### Task Data")
                        st.json({
                            "project_id": project_id,
                            "title": title,
                            "description": description,
                            "status": status,
                            "priority": priority,
                            "assignee": assignee,
                            "due_date": str(due_date)
                        })
                    
                    # Simple insert query
                    insert_query = '''
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, assignee, due_date)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    '''
                    values = (project_id, title, description, status, priority, assignee, due_date)
                    
                    # Show the query being executed
                    with debug_container:
                        st.code(insert_query, language="sql")
                        st.write("Values:", values)
                    
                    result = execute_query(insert_query, values)
                    
                    if result:
                        task_id = result[0]['id']
                        st.success(f"✅ Task created successfully! (ID: {task_id})")
                        
                        # Verify the task exists
                        verify = execute_query(
                            "SELECT * FROM tasks WHERE id = %s",
                            (task_id,)
                        )
                        if verify:
                            with debug_container:
                                st.write("### Created Task")
                                st.json(verify[0])
                            time.sleep(0.5)
                            st.rerun()
                            return True
                        else:
                            st.error("Task verification failed!")
                            return False
                    else:
                        st.error("Failed to create task!")
                        return False
                        
                except Exception as e:
                    st.error(f"Error creating task: {str(e)}")
                    with debug_container:
                        st.error("### Error Details")
                        st.code(f"Type: {type(e).__name__}\nDetails: {str(e)}")
                    return False
                    
    except Exception as e:
        st.error(f"Form error: {str(e)}")
        return False
