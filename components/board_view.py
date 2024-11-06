import streamlit as st
from database.connection import execute_query
from utils.file_handler import get_task_attachments
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    try:
        st.write("## Project Board")
        
        # Debug info
        st.write("Debug Information")
        st.write(f"Querying tasks for project {project_id}")
        
        # Get total tasks
        count = execute_query(
            "SELECT COUNT(*) as count FROM tasks WHERE project_id = %s",
            (project_id,)
        )
        st.write(f"Total tasks in project: {count[0]['count']}")
        
        # Simple task list
        tasks = execute_query('''
            SELECT id, title, description, status, created_at
            FROM tasks 
            WHERE project_id = %s
            ORDER BY created_at DESC
        ''', (project_id,))
        
        if tasks:
            for task in tasks:
                with st.container():
                    st.write(f"**{task['title']}**")
                    if task['description']:
                        st.write(task['description'])
                    st.write(f"Status: {task['status']}")
                    
                    # Show attachments if any
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
                                        mime=attachment['file_type']
                                    )
                            except Exception as e:
                                logger.error(f"Error loading attachment: {str(e)}")
                    st.write("---")
        else:
            st.info("No tasks found. Create your first task!")
            
    except Exception as e:
        logger.error(f"Error loading board: {str(e)}")
        st.error(f"Error loading board: {str(e)}")
