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
        logger.info(f"Found {len(dependencies) if dependencies else 0} dependencies for task {task_id}")
        return dependencies
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
        logger.info(f"Found {len(subtasks) if subtasks else 0} subtasks for task {task_id}")
        return subtasks
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
        execute_query("""
            UPDATE subtasks
            SET completed = %s, status = CASE WHEN %s THEN 'Done' ELSE 'To Do' END
            WHERE id = %s
            RETURNING id, status
        """, (completed, completed, subtask_id))
        logger.info(f"Updated subtask {subtask_id} status to {completed}")
        return True
    except Exception as e:
        logger.error(f"Error updating subtask {subtask_id}: {str(e)}")
        return False

def render_task_card(task, subtasks, dependencies, attachments):
    """Render a single task card with the new design"""
    with st.container():
        # Task header with expand/collapse
        col1, col2, col3 = st.columns([6,2,2])
        with col1:
            st.write(f"### {task['title']}")
        with col2:
            st.write(f"📅 {task['due_date'].strftime('%b %d') if task['due_date'] else 'No date'}")
        with col3:
            priority_colors = {
                'High': '🔴',
                'Medium': '🟡',
                'Low': '🟢'
            }
            st.write(f"{priority_colors.get(task['priority'], '⚪')} {task['priority']}")
        
        # Progress bar based on subtasks
        progress = calculate_task_progress(subtasks)
        st.progress(progress)

        # Status with color coding
        status_colors = {
            'To Do': '⚪ TO DO',
            'In Progress': '🔵 IN PROGRESS',
            'Done': '🟢 DONE'
        }
        st.write(status_colors.get(task['status'], task['status']))

        # Task details in collapsible section
        with st.expander("Details", expanded=False):
            if task['description']:
                st.write(task['description'])
            
            # Dependencies section
            if dependencies:
                st.markdown("**Dependencies:**")
                for dep in dependencies:
                    st.markdown(
                        f"- {dep['title']} ({dep['status']}) "
                        f"{priority_colors.get(dep['priority'], '⚪')}"
                    )
            
            # Subtasks section with checkboxes
            if subtasks:
                st.markdown("**Subtasks:**")
                for subtask in subtasks:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"- {subtask['title']}")
                    with col2:
                        if st.checkbox(
                            "Done", 
                            value=subtask['completed'],
                            key=f"subtask_{subtask['id']}"
                        ):
                            if update_subtask_status(subtask['id'], True):
                                st.rerun()
            
            # Attachments section
            if attachments:
                st.markdown("**Attachments:**")
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

def render_board(project_id):
    logger.info(f"Rendering board for project {project_id}")
    try:
        st.write("### Project Board")
        
        # Get project stats
        project_info = execute_query("""
            SELECT p.id, 
                   (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) as task_count
            FROM projects p 
            WHERE p.id = %s
        """, (project_id,))
        
        if project_info:
            logger.info(f"Project has {project_info[0]['task_count']} total tasks")
        
        # Add task creation button
        if st.button('➕ Create New Task'):
            if create_task_form(project_id):
                st.rerun()
        
        # Get all templates
        all_templates = {**DEFAULT_TEMPLATES, **get_board_templates()}
        
        # Fetch tasks with proper ordering and logging
        logger.info(f"Fetching tasks for project_id={project_id}")
        tasks = execute_query('''
            SELECT t.*
            FROM tasks t
            WHERE t.project_id = %s
            ORDER BY t.created_at DESC
        ''', (project_id,))
        
        if tasks:
            logger.info(f"Found {len(tasks)} tasks")
            
            # Get current statuses
            current_statuses = list(set(task['status'] for task in tasks))
            
            # Try to detect current template
            current_template = None
            for name, columns in all_templates.items():
                if set(current_statuses).issubset(set(columns)):
                    current_template = name
                    break
            
            if not current_template:
                current_template = "Basic Kanban"
            
            # Template selection
            selected_template = st.selectbox(
                "Select Board Template",
                options=list(all_templates.keys()),
                index=list(all_templates.keys()).index(current_template)
            )
            
            # Display Kanban Board
            board_columns = st.columns(len(all_templates[selected_template]))
            
            # Initialize tasks by status
            tasks_by_status = {status: [] for status in all_templates[selected_template]}
            
            # Group tasks by status
            for task in tasks:
                current_status = task['status']
                if current_status in tasks_by_status:
                    tasks_by_status[current_status].append(task)
                else:
                    # Move to first column if status doesn't match template
                    first_status = all_templates[selected_template][0]
                    tasks_by_status[first_status].append(task)
                    # Update task status in database
                    execute_query("""
                        UPDATE tasks SET status = %s WHERE id = %s
                    """, (first_status, task['id']))
            
            # Display columns
            for col, status in zip(board_columns, all_templates[selected_template]):
                with col:
                    st.write(f"### {status}")
                    
                    current_tasks = tasks_by_status.get(status, [])
                    logger.info(f"Found {len(current_tasks)} tasks with status '{status}'")
                    
                    for task in current_tasks:
                        # Get related data
                        dependencies = get_task_dependencies(task['id'])
                        subtasks = get_task_subtasks(task['id'])
                        attachments = get_task_attachments(task['id'])
                        
                        # Render task card with new design
                        render_task_card(task, subtasks, dependencies, attachments)
        else:
            st.info("No tasks found. Create your first task to get started!")
            
    except Exception as e:
        logger.error(f"Error rendering board: {str(e)}")
        st.error(f"Error loading board: {str(e)}")
