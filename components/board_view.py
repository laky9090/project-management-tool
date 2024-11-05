import streamlit as st
from database.connection import execute_query
from utils.file_handler import get_task_attachments
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    try:
        st.write(f"### Project {project_id} Board")
        
        # Get project info with task count
        project = execute_query('''
            SELECT p.id, 
                   (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) as task_count
            FROM projects p 
            WHERE p.id = %s
        ''', (project_id,))
        
        if not project:
            st.error("Project not found")
            return
            
        st.write(f"Total tasks: {project[0]['task_count']}")
        
        # Create columns for task statuses
        cols = st.columns(3)
        
        for idx, status in enumerate(['To Do', 'In Progress', 'Done']):
            with cols[idx]:
                st.subheader(status)
                
                # Get tasks for this status
                tasks = execute_query('''
                    SELECT id, title, description, status, priority,
                           due_date, created_at
                    FROM tasks 
                    WHERE project_id = %s AND status = %s
                    ORDER BY priority DESC, created_at DESC
                ''', (project_id, status))
                
                if tasks:
                    for task in tasks:
                        with st.container():
                            st.markdown(f'''
                                <div style="border:1px solid #ddd; padding:10px; margin:5px 0; border-radius:5px;">
                                    <h4>{task['title']}</h4>
                                    <p>{task['description'] or ''}</p>
                                    <div>Priority: {task['priority']}</div>
                                    <div>Due: {task['due_date'].strftime('%Y-%m-%d') if task['due_date'] else 'No date'}</div>
                                </div>
                            ''', unsafe_allow_html=True)
                            
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
