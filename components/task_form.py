import streamlit as st
from database.connection import execute_query

def create_task_form(project_id):
    with st.form("task_form"):
        st.write("### Create Task")
        
        # Debug display at top
        st.write(f"Debug: Creating task for project {project_id}")
        
        title = st.text_input("Title")
        status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
        
        submitted = st.form_submit_button("Create Task")
        
        if submitted and title:
            try:
                # Show what we're about to insert
                st.write("Debug: Inserting task:")
                st.json({
                    "project_id": project_id,
                    "title": title,
                    "status": status
                })
                
                result = execute_query(
                    'INSERT INTO tasks (project_id, title, status) VALUES (%s, %s, %s) RETURNING *',
                    (project_id, title, status)
                )
                
                if result:
                    st.success("Task created!")
                    st.write("Debug: Created task:", result[0])
                    st.rerun()
                    return True
                
                st.error("Failed to create task")
                return False
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                return False
    return False
