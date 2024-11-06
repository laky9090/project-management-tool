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
            SELECT t.id, t.title, t.status
            FROM tasks t
            JOIN task_dependencies td ON t.id = td.depends_on_id
            WHERE td.task_id = %s
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

def update_subtask_status(subtask_id, completed):
    """Update subtask completion status"""
    try:
        execute_query("""
            UPDATE subtasks
            SET completed = %s, status = CASE WHEN %s THEN 'Done' ELSE 'To Do' END
            WHERE id = %s
        """, (completed, completed, subtask_id))
        logger.info(f"Updated subtask {subtask_id} status to {completed}")
        return True
    except Exception as e:
        logger.error(f"Error updating subtask {subtask_id}: {str(e)}")
        return False

def render_board(project_id):
    try:
        st.write("### Project Board")
        
        # Add task creation button at the top
        if st.button('➕ Create New Task'):
            if create_task_form(project_id):
                st.rerun()
        
        # Get all templates
        all_templates = {**DEFAULT_TEMPLATES, **get_board_templates()}
        
        # Get tasks with all fields and proper ordering
        logger.info(f"Fetching tasks for project_id={project_id}")
        tasks = execute_query('''
            SELECT t.*
            FROM tasks t
            WHERE t.project_id = %s
            ORDER BY t.priority DESC, t.created_at DESC
        ''', (project_id,))
        
        if tasks:
            logger.info(f"Found {len(tasks)} tasks")
            for task in tasks:
                logger.info(f"Task: {task['id']} - {task['title']} - {task['status']}")
            
            # Get current statuses
            current_statuses = list(set(task['status'] for task in tasks))
            
            # Try to detect current template
            current_template = None
            for name, columns in all_templates.items():
                if set(current_statuses).issubset(set(columns)):
                    current_template = name
                    break
                    
            if not current_template:
                current_template = "Basic Kanban"  # Default template
                
            # Template selection
            selected_template = st.selectbox(
                "Select Template",
                options=list(all_templates.keys()),
                index=list(all_templates.keys()).index(current_template),
                key="board_template"
            )
            
            # Display Kanban Board
            board_columns = st.columns(len(all_templates[selected_template]))
            
            # Initialize tasks_by_status with all possible statuses
            tasks_by_status = {status: [] for status in all_templates[selected_template]}
            
            # Group tasks by status
            for task in tasks:
                if task['status'] in tasks_by_status:
                    tasks_by_status[task['status']].append(task)
                else:
                    # If task status doesn't match template, move to first column
                    tasks_by_status[all_templates[selected_template][0]].append(task)
            
            # Display tasks in columns
            for col, status in zip(board_columns, all_templates[selected_template]):
                with col:
                    st.write(f"### {status}")
                    st.write(f"({len(tasks_by_status[status])} tasks)")
                    
                    for task in tasks_by_status[status]:
                        with st.container():
                            # Task card with colored border based on priority
                            priority_colors = {
                                "Low": "#28a745",
                                "Medium": "#ffc107",
                                "High": "#dc3545"
                            }
                            priority = task.get('priority', 'Medium')
                            
                            st.markdown(f"""
                                <div style="
                                    border-left: 4px solid {priority_colors[priority]};
                                    padding: 10px;
                                    margin: 5px 0;
                                    background: white;
                                    border-radius: 4px;
                                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                                    <strong>{task['title']}</strong>
                                    <p style="margin: 5px 0; font-size: 0.9em;">{task['description']}</p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Dependencies
                            dependencies = get_task_dependencies(task['id'])
                            if dependencies:
                                st.markdown("**Dependencies:**")
                                for dep in dependencies:
                                    st.markdown(f"- {dep['title']} ({dep['status']})")
                            
                            # Subtasks
                            subtasks = get_task_subtasks(task['id'])
                            if subtasks:
                                st.markdown("**Subtasks:**")
                                for subtask in subtasks:
                                    col1, col2 = st.columns([4, 1])
                                    with col1:
                                        st.markdown(f"- {subtask['title']}")
                                    with col2:
                                        if st.checkbox("Done", value=subtask['completed'], key=f"subtask_{subtask['id']}"):
                                            if update_subtask_status(subtask['id'], True):
                                                st.rerun()
                            
                            # Show attachments if any
                            attachments = get_task_attachments(task['id'])
                            if attachments:
                                st.markdown("📎 Attachments:")
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
            
    except Exception as e:
        logger.error(f"Error fetching tasks: {str(e)}")
        st.error(f"Error loading tasks: {str(e)}")
        return
