import streamlit as st
from database.connection import execute_query
from utils.file_handler import get_task_attachments
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    st.write("### Project Board")
    st.write(f"Debug: Viewing tasks for project {project_id}")
    
    # Raw query to get all tasks
    tasks = execute_query('SELECT * FROM tasks WHERE project_id = %s', (project_id,))
    
    st.write(f"Debug: Found {len(tasks) if tasks else 0} total tasks")
    if tasks:
        st.write("### Raw Task Data:")
        for task in tasks:
            st.write("---")
            st.write("Task:", task)
            
            # Display attachments
            attachments = get_task_attachments(task['id'])
            if attachments:
                st.write("Attachments:")
                for attachment in attachments:
                    st.write("Attachment data:", attachment)
                    with open(attachment['file_path'], 'rb') as f:
                        st.download_button(
                            f"📄 {attachment['filename']}",
                            f,
                            file_name=attachment['filename'],
                            mime=attachment['file_type']
                        )
    else:
        st.info("No tasks found for this project")
