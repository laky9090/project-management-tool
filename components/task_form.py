import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging
import time

logger = logging.getLogger(__name__)

def get_project_tasks(project_id, exclude_task_id=None):
    """Get all tasks in a project except the specified task"""
    try:
        query = """
            SELECT id, title, status 
            FROM tasks 
            WHERE project_id = %s
        """
        params = [project_id]
        
        if exclude_task_id:
            query += " AND id != %s"
            params.append(exclude_task_id)
            
        return execute_query(query, params)
    except Exception as e:
        logger.error(f"Error fetching project tasks: {str(e)}")
        return []

def create_task_form(project_id):
    try:
        with st.form("task_form"):
            st.write("### Create New Task")
            
            # Basic task information
            title = st.text_input("Title", key="task_title")
            description = st.text_area("Description", key="task_desc")
            
            # Task metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            with col2:
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            with col3:
                due_date = st.date_input("Due Date")
                
            # Dependencies section
            st.write("### Dependencies")
            available_tasks = get_project_tasks(project_id)
            dependencies = []
            if available_tasks:
                dependencies = st.multiselect(
                    "This task depends on",
                    options=[(t['id'], f"{t['title']} ({t['status']})") for t in available_tasks],
                    format_func=lambda x: x[1]
                )
                
            # Subtasks section
            st.write("### Subtasks")
            num_subtasks = st.number_input("Number of subtasks", min_value=0, max_value=10, value=0)
            subtasks = []
            
            for i in range(num_subtasks):
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        subtask_title = st.text_input(f"Subtask {i+1} Title", key=f"subtask_title_{i}")
                    with col2:
                        subtask_status = st.selectbox(
                            "Status",
                            ["To Do", "Done"],
                            key=f"subtask_status_{i}"
                        )
                    subtask_desc = st.text_area(f"Description", key=f"subtask_desc_{i}")
                    if subtask_title:
                        subtasks.append({
                            'title': subtask_title,
                            'description': subtask_desc,
                            'completed': subtask_status == "Done"
                        })
            
            # File attachment
            uploaded_file = st.file_uploader(
                "Attach File (optional)",
                type=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx']
            )
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted and title:
                try:
                    # Start transaction
                    execute_query("BEGIN")
                    
                    # Create main task
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status, priority, due_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id, title;
                    ''', (project_id, title, description, status, priority, due_date))
                    
                    if not result:
                        raise Exception("Failed to create task")
                        
                    task_id = result[0]['id']
                    
                    # Add dependencies
                    if dependencies:
                        for dep_id, _ in dependencies:
                            dep_result = execute_query('''
                                INSERT INTO task_dependencies (task_id, depends_on_id)
                                VALUES (%s, %s)
                                RETURNING id
                            ''', (task_id, dep_id))
                            if not dep_result:
                                raise Exception("Failed to add dependencies")
                    
                    # Add subtasks
                    if subtasks:
                        for subtask in subtasks:
                            subtask_result = execute_query('''
                                INSERT INTO subtasks (parent_task_id, title, description, completed)
                                VALUES (%s, %s, %s, %s)
                                RETURNING id
                            ''', (task_id, subtask['title'], subtask['description'], subtask['completed']))
                            if not subtask_result:
                                raise Exception("Failed to create subtask")
                    
                    # Handle file upload
                    if uploaded_file:
                        file_id = save_uploaded_file(uploaded_file, task_id)
                        if not file_id:
                            raise Exception("Failed to save attachment")
                    
                    # Commit transaction
                    execute_query("COMMIT")
                    st.success(f"✅ Task '{title}' created successfully!")
                    time.sleep(0.5)  # Ensure transaction completes
                    st.rerun()
                    return True
                    
                except Exception as e:
                    execute_query("ROLLBACK")
                    st.error(f"Error creating task: {str(e)}")
                    return False
                    
    except Exception as e:
        st.error(f"Form error: {str(e)}")
        return False
    
    return False
