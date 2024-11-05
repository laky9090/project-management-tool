import streamlit as st
from database.connection import execute_query
from utils.file_handler import get_task_attachments
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    st.write("### Project Board")
    st.write(f"Viewing tasks for project {project_id}")
    
    # Get task count
    count_result = execute_query('''
        SELECT COUNT(*) as count FROM tasks WHERE project_id = %s
    ''', (project_id,))
    
    if count_result:
        st.write(f"Total tasks: {count_result[0]['count']}")
    
    # Display tasks by status
    for status in ["To Do", "In Progress", "Done"]:
        st.subheader(status)
        tasks = execute_query('''
            SELECT id, title, description, status, created_at 
            FROM tasks 
            WHERE project_id = %s AND status = %s
            ORDER BY created_at DESC
        ''', (project_id, status))
        
        if tasks:
            for task in tasks:
                with st.container():
                    st.write(f"**{task['title']}**")
                    if task['description']:
                        st.write(task['description'])
                    st.write(f"Created: {task['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    
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
            st.info(f"No tasks in {status}")
