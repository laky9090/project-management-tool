import streamlit as st
from database.connection import execute_query
from utils.file_handler import get_task_attachments
from components.task_form import create_task_form
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    try:
        logger.info(f"Rendering board for project {project_id}")
        
        # Get project info first to verify it exists
        project = execute_query('''
            SELECT p.id, 
                   (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) as task_count
            FROM projects p 
            WHERE p.id = %s
        ''', (project_id,))
        
        if not project:
            st.error("Project not found")
            return
            
        logger.info(f"Project has {project[0]['task_count']} total tasks")
        
        # Create task button with unique key
        if st.button("➕ Add Task", key=f"add_task_btn_{project_id}"):
            create_task_form(project_id)
        
        # Render board columns
        cols = st.columns(3)
        
        for idx, status in enumerate(['To Do', 'In Progress', 'Done']):
            with cols[idx]:
                st.subheader(status)
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
                            st.markdown(f"**{task['title']}**")
                            if task['description']:
                                st.write(task['description'])
                            st.write(f"Priority: {task['priority']}")
                            if task['due_date']:
                                st.write(f"Due: {task['due_date']}")
                            
                            # Display attachments if any
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
                                                key=f"download_btn_{attachment['id']}"
                                            )
                                    except Exception as e:
                                        logger.error(f"Error loading attachment: {str(e)}")
                                        st.warning(f"Could not load attachment: {attachment['filename']}")
                else:
                    st.info(f"No tasks in {status}")
                    
    except Exception as e:
        logger.error(f"Error in board view: {str(e)}")
        st.error("An error occurred while loading the Board view. Please try again.")
