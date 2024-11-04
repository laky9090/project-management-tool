import streamlit as st
from database.connection import execute_query
from datetime import datetime

def create_task_form(project_id):
    with st.form("task_form"):
        st.write("Create New Task")
        title = st.text_input("Task Title")
        description = st.text_area("Description")
        status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        assignee = st.text_input("Assignee")
        due_date = st.date_input("Due Date", min_value=datetime.today())
        
        submitted = st.form_submit_button("Create Task")
        
        if submitted:
            if not title:
                st.error("Task title is required!")
                return False
                
            try:
                result = execute_query("""
                    INSERT INTO tasks (project_id, title, description, status, 
                                     priority, assignee, due_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (project_id, title, description, status, priority, assignee, due_date))
                
                if result:
                    st.success("Task created successfully!")
                    return True
                else:
                    st.error("Failed to create task. Please try again.")
                    return False
                    
            except Exception as e:
                st.error(f"Error creating task: {str(e)}")
                return False
    return False
