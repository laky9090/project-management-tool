import streamlit as st
from database.connection import execute_query
from utils.file_handler import get_task_attachments
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    try:
        st.write(f"### Project {project_id} Board")
        
        # Get all tasks for debugging
        st.write("### Debug: Querying tasks")
        tasks = execute_query('''
            SELECT * FROM tasks 
            WHERE project_id = %s
            ORDER BY created_at DESC
        ''', (project_id,))
        
        st.write(f"Found {len(tasks) if tasks else 0} total tasks")
        
        if tasks:
            st.write("### Task Data:")
            for task in tasks:
                with st.container():
                    st.markdown(f'''
                        <div style="border: 1px solid #ccc; padding: 10px; margin: 5px 0;">
                            <h4>{task['title']}</h4>
                            <p>{task['description']}</p>
                            <p>Status: {task['status']}</p>
                            <p>Created: {task['created_at']}</p>
                        </div>
                    ''', unsafe_allow_html=True)
                    
                    # Display attachments
                    attachments = get_task_attachments(task['id'])
                    if attachments:
                        st.write("📎 Attachments:")
                        for attachment in attachments:
                            with open(attachment['file_path'], 'rb') as f:
                                st.download_button(
                                    f"📄 {attachment['filename']}",
                                    f,
                                    file_name=attachment['filename'],
                                    mime=attachment['file_type']
                                )
        else:
            st.info("No tasks found")
            
    except Exception as e:
        st.error(f"Error rendering board: {str(e)}")
