import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file
import logging
import time

logger = logging.getLogger(__name__)

def get_project_tasks(project_id, exclude_task_id=None):
    """Get all tasks in a project except the specified task"""
    query = """
        SELECT id, title 
        FROM tasks 
        WHERE project_id = %s
    """
    params = [project_id]
    
    if exclude_task_id:
        query += " AND id != %s"
        params.append(exclude_task_id)
        
    return execute_query(query, params)

def create_task_form(project_id):
    logger.info(f"Creating task for project: {project_id}")
    try:
        with st.form("task_form"):
            st.write("### Add Task")
            
            # Main task fields
            title = st.text_input("Title", key=f"title_{project_id}")
            description = st.text_area("Description", key=f"desc_{project_id}")
            
            col1, col2 = st.columns(2)
            with col1:
                status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            
            # Dependencies section
            st.write("### Dependencies")
            available_tasks = get_project_tasks(project_id)
            if available_tasks:
                dependencies = st.multiselect(
                    "This task depends on",
                    options=[(t['id'], t['title']) for t in available_tasks],
                    format_func=lambda x: x[1]
                )
            
            # Subtasks section
            st.write("### Subtasks")
            num_subtasks = st.number_input("Number of subtasks", min_value=0, max_value=10, value=0)
            subtasks = []
            
            for i in range(num_subtasks):
                with st.container():
                    st.write(f"Subtask {i+1}")
                    subtask_title = st.text_input(f"Title###{i}", key=f"subtask_title_{i}")
                    subtask_desc = st.text_area(f"Description###{i}", key=f"subtask_desc_{i}")
                    if subtask_title:
                        subtasks.append({
                            'title': subtask_title,
                            'description': subtask_desc
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
                        INSERT INTO tasks (project_id, title, description, status, priority)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id, title;
                    ''', (project_id, title, description, status, priority))
                    
                    if result:
                        task_id = result[0]['id']
                        logger.info(f"Created task {task_id} for project {project_id}")
                        
                        # Add dependencies
                        if available_tasks and dependencies:
                            for dep_id, _ in dependencies:
                                execute_query('''
                                    INSERT INTO task_dependencies (task_id, depends_on_id)
                                    VALUES (%s, %s)
                                ''', (task_id, dep_id))
                                logger.info(f"Added dependency: Task {task_id} depends on {dep_id}")
                        
                        # Add subtasks
                        for subtask in subtasks:
                            subtask_result = execute_query('''
                                INSERT INTO subtasks (parent_task_id, title, description)
                                VALUES (%s, %s, %s)
                                RETURNING id
                            ''', (task_id, subtask['title'], subtask['description']))
                            if subtask_result:
                                logger.info(f"Created subtask: {subtask_result[0]['id']} for task {task_id}")
                        
                        # Handle file upload
                        if uploaded_file:
                            file_id = save_uploaded_file(uploaded_file, task_id)
                            if file_id:
                                logger.info(f"Attached file: {uploaded_file.name} to task {task_id}")
                                st.success(f"✅ File '{uploaded_file.name}' attached!")
                        
                        execute_query("COMMIT")
                        st.success(f"✅ Task '{title}' created successfully!")
                        # Add delay to ensure DB operations complete
                        time.sleep(0.5)
                        st.rerun()
                        return True
                    
                    execute_query("ROLLBACK")
                    st.error("Failed to create task - database error")
                    return False
                    
                except Exception as e:
                    execute_query("ROLLBACK")
                    logger.error(f"Error creating task: {str(e)}")
                    st.error(f"Error creating task: {str(e)}")
                    return False
                    
        return False
        
    except Exception as e:
        logger.error(f"Form error: {str(e)}")
        st.error(f"Form error: {str(e)}")
        return False
