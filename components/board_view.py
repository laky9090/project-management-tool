import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file, get_task_attachments
from components.task_form import create_task_form
import logging
import time

logger = logging.getLogger(__name__)

def get_task_dependencies(task_id):
    """Get dependencies for a task"""
    try:
        logger.info(f"Fetching dependencies for task {task_id}")
        dependencies = execute_query("""
            SELECT t.id, t.title, t.status, t.priority
            FROM tasks t
            JOIN task_dependencies td ON t.id = td.depends_on_id
            WHERE td.task_id = %s
            ORDER BY t.created_at DESC
        """, (task_id,))
        logger.info(f"Found {len(dependencies) if dependencies else 0} dependencies")
        return dependencies if dependencies else []
    except Exception as e:
        logger.error(f"Error fetching dependencies for task {task_id}: {str(e)}")
        return []

def get_task_subtasks(task_id):
    """Get subtasks for a task"""
    try:
        logger.info(f"Fetching subtasks for task {task_id}")
        subtasks = execute_query("""
            SELECT id, title, description, status, completed
            FROM subtasks
            WHERE parent_task_id = %s
            ORDER BY created_at
        """, (task_id,))
        logger.info(f"Found {len(subtasks) if subtasks else 0} subtasks")
        return subtasks if subtasks else []
    except Exception as e:
        logger.error(f"Error fetching subtasks for task {task_id}: {str(e)}")
        return []

def update_subtask_status(subtask_id, completed):
    """Update subtask completion status"""
    try:
        execute_query("BEGIN")
        result = execute_query("""
            UPDATE subtasks
            SET completed = %s,
                status = CASE WHEN %s THEN 'Done' ELSE 'To Do' END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, title, status
        """, (completed, completed, subtask_id))
        
        if result:
            execute_query("COMMIT")
            return True
        else:
            execute_query("ROLLBACK")
            return False
    except Exception as e:
        execute_query("ROLLBACK")
        logger.error(f"Error updating subtask status: {str(e)}")
        return False

def render_task_card(task):
    """Render individual task card"""
    try:
        # Start explicit transaction
        execute_query("BEGIN")
        
        cols = st.columns([3, 2, 2, 2, 2])
        with cols[0]:
            st.write(f"**{task['title']}**")
            if task['description']:
                with st.expander("Description"):
                    st.write(task['description'])
        
        with cols[1]:
            new_status = st.selectbox(
                "Status",
                ["To Do", "In Progress", "Done"],
                index=["To Do", "In Progress", "Done"].index(task['status']),
                key=f"status_{task['id']}"
            )
            if new_status != task['status']:
                result = execute_query('''
                    UPDATE tasks 
                    SET status = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, title, status;
                ''', (new_status, task['id']))
                
                if result:
                    execute_query("COMMIT")
                    st.success(f"Updated status to {new_status}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    execute_query("ROLLBACK")
                    st.error("Failed to update status")
        
        with cols[2]:
            new_priority = st.selectbox(
                "Priority",
                ["Low", "Medium", "High"],
                index=["Low", "Medium", "High"].index(task['priority']),
                key=f"priority_{task['id']}"
            )
            if new_priority != task['priority']:
                result = execute_query('''
                    UPDATE tasks 
                    SET priority = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, title, priority;
                ''', (new_priority, task['id']))
                
                if result:
                    execute_query("COMMIT")
                    st.success(f"Updated priority to {new_priority}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    execute_query("ROLLBACK")
                    st.error("Failed to update priority")
        
        with cols[3]:
            new_due_date = st.date_input(
                "Due Date",
                value=task['due_date'] if task['due_date'] else None,
                key=f"due_date_{task['id']}"
            )
            if new_due_date != task['due_date']:
                result = execute_query('''
                    UPDATE tasks 
                    SET due_date = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, title;
                ''', (new_due_date, task['id']))
                
                if result:
                    execute_query("COMMIT")
                    st.success("Updated due date")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    execute_query("ROLLBACK")
                    st.error("Failed to update due date")
        
        # Details section
        with cols[4]:
            with st.expander("Details"):
                # Dependencies section
                dependencies = get_task_dependencies(task['id'])
                if dependencies:
                    st.write("**Dependencies:**")
                    for dep in dependencies:
                        st.write(f"- {dep['title']} ({dep['status']})")
                
                # Subtasks section
                subtasks = get_task_subtasks(task['id'])
                if subtasks:
                    st.write("**Subtasks:**")
                    for subtask in subtasks:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"- {subtask['title']}")
                        with col2:
                            if st.checkbox("Done", value=subtask['completed'], 
                                         key=f"subtask_{subtask['id']}"):
                                if update_subtask_status(subtask['id'], True):
                                    st.rerun()
                
                # Attachments section
                attachments = get_task_attachments(task['id'])
                if attachments:
                    st.write("**Attachments:**")
                    for attachment in attachments:
                        try:
                            with open(attachment['file_path'], 'rb') as f:
                                st.download_button(
                                    f"📎 {attachment['filename']}", 
                                    f,
                                    file_name=attachment['filename'],
                                    mime=attachment['file_type']
                                )
                        except Exception as e:
                            logger.error(f"Error loading attachment: {str(e)}")
        
        execute_query("COMMIT")
        
    except Exception as e:
        execute_query("ROLLBACK")
        logger.error(f"Error updating task: {str(e)}")
        st.error(f"Error updating task: {str(e)}")

def render_board(project_id):
    """Render project board"""
    st.write("### Project Board")
    
    # Add task creation button at top
    if st.button('➕ Create New Task'):
        if create_task_form(project_id):
            st.rerun()
            return

    # Create columns for the board
    cols = st.columns([3, 2, 2, 2, 2])
    with cols[0]:
        st.write("**Task**")
    with cols[1]:
        st.write("**Status**")
    with cols[2]:
        st.write("**Priority**")
    with cols[3]:
        st.write("**Due Date**")
    with cols[4]:
        st.write("**Details**")

    # Fetch tasks
    logger.info(f"Fetching tasks for project {project_id}")
    tasks = execute_query('''
        SELECT t.*
        FROM tasks t
        WHERE t.project_id = %s
        ORDER BY t.created_at DESC
    ''', (project_id,))
    
    if tasks:
        logger.info(f"Found {len(tasks)} tasks")
        for task in tasks:
            logger.info(f"Processing task: {task['id']} - {task['title']} - {task['status']}")
            render_task_card(task)
    else:
        st.info("No tasks found. Create your first task to get started!")
