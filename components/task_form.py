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
    """Create new task form with transaction handling"""
    # Initialize subtask count if not exists
    if 'subtask_count' not in st.session_state:
        st.session_state.subtask_count = 1

    # Add subtask button (outside the form)
    if st.button("+ Add Another Subtask"):
        st.session_state.subtask_count += 1
        st.rerun()

    try:
        with st.form("task_form"):
            st.write("### Create New Task")
            
            # Basic task information
            title = st.text_input("Title")
            description = st.text_area("Description")
            
            # Task metadata
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            with col2:
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            with col3:
                due_date = st.date_input("Due Date")
            with col4:
                assignee = st.text_input("Assignee")
            
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
            subtasks = []
            for i in range(st.session_state.subtask_count):
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
            
            # Submit button
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("Task title is required")
                    return False
                    
                try:
                    logger.info(f"Starting task creation for project {project_id}")
                    
                    # Start transaction
                    execute_query("BEGIN")
                    
                    # Create main task
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status, priority, due_date, assignee)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    ''', (project_id, title, description, status, priority, due_date, assignee))
                    
                    if not result:
                        raise Exception("Failed to create task")
                        
                    task_id = result[0]['id']
                    logger.info(f"Created task with ID {task_id}")
                    
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
                        logger.info(f"Added {len(subtasks)} subtasks to task {task_id}")
                    
                    # Handle file upload
                    if uploaded_file:
                        file_id = save_uploaded_file(uploaded_file, task_id)
                        if not file_id:
                            raise Exception("Failed to save attachment")
                        logger.info(f"Added attachment to task {task_id}")
                    
                    # Commit transaction
                    execute_query("COMMIT")
                    st.success(f"✅ Task '{title}' created successfully!")
                    
                    # Reset form state
                    st.session_state.subtask_count = 1
                    st.session_state.show_task_form = False
                    
                    time.sleep(0.5)
                    return True
                    
                except Exception as e:
                    execute_query("ROLLBACK")
                    logger.error(f"Error creating task: {str(e)}")
                    st.error(f"Failed to create task: {str(e)}")
                    return False
                    
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        return False
    
    return False