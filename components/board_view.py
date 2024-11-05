import streamlit as st
from database.connection import execute_query
from utils.file_handler import get_task_attachments
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    st.write(f"Tasks for Project {project_id}")
    
    # Get tasks with their attachments
    tasks = execute_query('''
        SELECT t.*, array_agg(fa.filename) as attachment_files
        FROM tasks t
        LEFT JOIN file_attachments fa ON t.id = fa.task_id
        WHERE t.project_id = %s
        GROUP BY t.id
        ORDER BY t.created_at DESC
    ''', (project_id,))
    
    if tasks:
        # Group tasks by status
        task_groups = {'To Do': [], 'In Progress': [], 'Done': []}
        for task in tasks:
            if task['status'] in task_groups:
                task_groups[task['status']].append(task)
        
        # Create columns for each status
        columns = st.columns(len(task_groups))
        
        for idx, (status, status_tasks) in enumerate(task_groups.items()):
            with columns[idx]:
                st.subheader(status)
                
                if status_tasks:
                    for task in status_tasks:
                        with st.container():
                            st.write("---")
                            st.write(f"**{task['title']}**")
                            if task['description']:
                                st.write(task['description'])
                            
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
                                                mime=attachment['file_type']
                                            )
                                    except Exception as e:
                                        st.warning(f"Could not load attachment: {attachment['filename']}")
                else:
                    st.info(f"No tasks in {status}")
    else:
        st.info("No tasks found")
