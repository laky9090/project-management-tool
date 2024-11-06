import streamlit as st
from database.connection import execute_query
from utils.file_handler import get_task_attachments
from components.task_form import create_task_form
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    try:
        logger.info(f"Rendering board for project {project_id}")
        
        # Verify task count
        logger.info(f"Verifying task count for project {project_id}")
        count_result = execute_query(
            "SELECT COUNT(*) as task_count FROM tasks WHERE project_id = %s",
            (project_id,)
        )
        if count_result:
            logger.info(f"Total tasks in database: {count_result[0]['task_count']}")
        
        # Add task creation button
        if st.button("➕ Add Task", type="primary", use_container_width=True):
            create_task_form(project_id)
            
        # Get project info with task count
        project = execute_query('''
            SELECT p.id, 
                   (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) as task_count
            FROM projects p 
            WHERE p.id = %s
        ''', (project_id,))
        
        if not project:
            logger.error(f"Project {project_id} not found")
            st.error("Project not found")
            return
        
        # Create columns for task statuses
        cols = st.columns(3)
        
        for idx, status in enumerate(['To Do', 'In Progress', 'Done']):
            with cols[idx]:
                st.subheader(status)
                
                # Get tasks for this status
                logger.info(f"Fetching tasks for project_id={project_id}, status={status}")
                tasks = execute_query('''
                    SELECT id, title, description, status, priority,
                           due_date, created_at 
                    FROM tasks 
                    WHERE project_id = %s AND status = %s
                    ORDER BY priority DESC, created_at DESC
                ''', (project_id, status))
                
                logger.info(f"Found {len(tasks) if tasks else 0} tasks with status '{status}'")
                
                if tasks:
                    for task in tasks:
                        with st.container():
                            # Task card with styling
                            st.markdown(f'''
                                <div style="
                                    border: 1px solid #ddd;
                                    border-radius: 5px;
                                    padding: 10px;
                                    margin: 5px 0;
                                    background-color: white;
                                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                                    <h4 style="margin: 0 0 8px 0;">{task['title']}</h4>
                                    <p style="margin: 0 0 8px 0; color: #666;">{task['description'] or ''}</p>
                                    <div style="
                                        display: inline-block;
                                        padding: 2px 8px;
                                        border-radius: 12px;
                                        background-color: {
                                            '#dc3545' if task['priority'] == 'High'
                                            else '#ffc107' if task['priority'] == 'Medium'
                                            else '#28a745'
                                        };
                                        color: white;
                                        font-size: 12px;
                                        margin-bottom: 8px;">
                                        {task['priority']}
                                    </div>
                                    <div style="color: #666; font-size: 12px;">
                                        Due: {task['due_date'].strftime('%Y-%m-%d') if task['due_date'] else 'No date'}
                                    </div>
                                </div>
                            ''', unsafe_allow_html=True)
                            
                            # Display attachments
                            attachments = get_task_attachments(task['id'])
                            if attachments:
                                st.write("📎 Attachments:")
                                for attachment in attachments:
                                    try:
                                        with open(attachment['file_path'], 'rb') as f:
                                            st.download_button(
                                                f"📄 {attachment['filename']}", 
                                                f,
                                                file_name=attachment['filename'],
                                                mime=attachment['file_type'],
                                                key=f"download_{task['id']}_{attachment['id']}"
                                            )
                                    except Exception as e:
                                        logger.error(f"Error loading attachment: {str(e)}")
                                        st.warning(f"Could not load attachment: {attachment['filename']}")
                else:
                    st.info(f"No tasks in {status}")
                    
    except Exception as e:
        logger.error(f"Error in board view: {str(e)}")
        st.error("An error occurred while loading the board. Please try again.")
