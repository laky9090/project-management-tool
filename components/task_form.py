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
        
        if submitted and title:
            execute_query("""
                INSERT INTO tasks (project_id, title, description, status, 
                                 priority, assignee, due_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (project_id, title, description, status, priority, assignee, due_date))
            st.success("Task created successfully!")
            return True
    return False
