import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file, get_task_attachments
from components.board_templates import get_board_templates, DEFAULT_TEMPLATES
from components.task_form import create_task_form
import logging

logger = logging.getLogger(__name__)

def get_task_dependencies(task_id):
    """Get dependencies for a task"""
    try:
        dependencies = execute_query("""
            SELECT t.id, t.title, t.status, t.priority
            FROM tasks t
            JOIN task_dependencies td ON t.id = td.depends_on_id
            WHERE td.task_id = %s
            ORDER BY t.created_at DESC
        """, (task_id,))
        return dependencies if dependencies else []
    except Exception as e:
        logger.error(f"Error fetching dependencies for task {task_id}: {str(e)}")
        return []

def get_task_subtasks(task_id):
    """Get subtasks for a task"""
    try:
        subtasks = execute_query("""
            SELECT id, title, description, status, completed
            FROM subtasks
            WHERE parent_task_id = %s
            ORDER BY created_at
        """, (task_id,))
        return subtasks if subtasks else []
    except Exception as e:
        logger.error(f"Error fetching subtasks for task {task_id}: {str(e)}")
        return []

def calculate_task_progress(subtasks):
    """Calculate task progress based on completed subtasks"""
    if not subtasks:
        return 0
    completed = sum(1 for subtask in subtasks if subtask['completed'])
    return completed / len(subtasks)

def update_subtask_status(subtask_id, completed):
    """Update subtask completion status"""
    try:
        logger.info(f"Updating subtask {subtask_id} status to {'completed' if completed else 'incomplete'}")
        execute_query("""
            UPDATE subtasks
            SET completed = %s, status = CASE WHEN %s THEN 'Done' ELSE 'To Do' END
            WHERE id = %s
        """, (completed, completed, subtask_id))
        logger.info(f"Subtask {subtask_id} status updated successfully")
        return True
    except Exception as e:
        logger.error(f"Error updating subtask {subtask_id}: {str(e)}")
        return False

def render_board(project_id):
    logger.info(f"Rendering board for project {project_id}")
    
    st.write("### Project Board")
    
    # Add task creation button
    if st.button('➕ Create New Task'):
        if create_task_form(project_id):
            st.rerun()

    # Create columns for the board header
    cols = st.columns([3, 2, 2, 2, 2, 2])
    with cols[0]:
        st.write("**Task Name**")
    with cols[1]:
        st.write("**Status**")
    with cols[2]:
        st.write("**Priority**")
    with cols[3]:
        st.write("**Due Date**")
    with cols[4]:
        st.write("**Note**")
    with cols[5]:
        st.write("**Docs**")

    # Fetch tasks with dependencies and subtasks
    logger.info(f"Fetching tasks for project {project_id}")
    tasks = execute_query('''
        SELECT t.*,
               COUNT(DISTINCT td.depends_on_id) as dependency_count,
               COUNT(DISTINCT s.id) as subtask_count
        FROM tasks t
        LEFT JOIN task_dependencies td ON t.id = td.task_id
        LEFT JOIN subtasks s ON t.id = s.parent_task_id
        WHERE t.project_id = %s
        GROUP BY t.id
        ORDER BY t.created_at DESC
    ''', (project_id,))
    
    logger.info(f"Found {len(tasks) if tasks else 0} tasks")
    if tasks:
        for task in tasks:
            logger.info(f"Task: {task['id']} - {task['title']} - {task['status']}")
            
            # Get dependencies and subtasks
            dependencies = get_task_dependencies(task['id'])
            subtasks = get_task_subtasks(task['id'])
            attachments = get_task_attachments(task['id'])
            
            # Calculate progress
            progress = calculate_task_progress(subtasks)
            logger.info(f"Task {task['id']} progress: {progress:.0%}")
            
            cols = st.columns([3, 2, 2, 2, 2, 2])
            with cols[0]:
                title_text = f"**{task['title']}**"
                if task['subtask_count'] > 0:
                    title_text += f" ({len([s for s in subtasks if s['completed']])}/{len(subtasks)})"
                st.write(title_text)
                
                # Display progress bar if has subtasks
                if subtasks:
                    st.progress(progress)

            with cols[1]:
                status_colors = {
                    'Done': '🟢',
                    'In Progress': '🟡',
                    'To Do': '⚪'
                }
                st.write(f"{status_colors.get(task['status'], '⚪')} {task['status']}")

            with cols[2]:
                priority_colors = {
                    'High': '🔴',
                    'Medium': '🟡',
                    'Low': '🟢'
                }
                st.write(f"{priority_colors.get(task['priority'], '⚪')} {task['priority']}")

            with cols[3]:
                st.write(task['due_date'].strftime('%b %d') if task['due_date'] else '-')

            with cols[4]:
                if task['description']:
                    with st.expander("📝"):
                        st.write(task['description'])
                        
                        # Display dependencies
                        if dependencies:
                            st.write("**Dependencies:**")
                            for dep in dependencies:
                                st.write(f"- {dep['title']} ({dep['status']})")
                        
                        # Display subtasks
                        if subtasks:
                            st.write("**Subtasks:**")
                            for subtask in subtasks:
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.write(f"- {subtask['title']}")
                                with col2:
                                    if st.checkbox("Done", value=subtask['completed'], key=f"subtask_{subtask['id']}"):
                                        if update_subtask_status(subtask['id'], True):
                                            st.rerun()

            with cols[5]:
                if attachments:
                    with st.expander("📄"):
                        for attachment in attachments:
                            try:
                                with open(attachment['file_path'], 'rb') as f:
                                    st.download_button(
                                        f"📄 {attachment['filename']}", 
                                        f,
                                        file_name=attachment['filename'],
                                        mime=attachment['file_type']
                                    )
                            except Exception as e:
                                logger.error(f"Error loading attachment: {str(e)}")
    else:
        st.info("No tasks found. Create your first task to get started!")
