import streamlit as st
from database.connection import execute_query
from utils.file_handler import get_task_attachments, delete_attachment
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    logger.info(f"Rendering board for project {project_id}")
    
    # Get total task count
    task_count = execute_query('''
        SELECT p.id, 
               (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) as task_count
        FROM projects p 
        WHERE p.id = %s
    ''', (project_id,))
    
    if task_count:
        logger.info(f"Project has {task_count[0]['task_count']} total tasks")
    
    # Display tasks by status
    for status in ["To Do", "In Progress", "Done"]:
        st.subheader(status)
        tasks = execute_query('''
            SELECT id, title, description, status, priority, 
                   assignee, due_date, created_at 
            FROM tasks 
            WHERE project_id = %s AND status = %s
            ORDER BY priority DESC, created_at DESC
        ''', (project_id, status))
        
        logger.info(f"Found {len(tasks) if tasks else 0} tasks with status '{status}'")
        
        if tasks:
            for task in tasks:
                with st.container():
                    # Task header with title and description
                    st.markdown(f"""
                        <div style='
                            background: white;
                            padding: 1rem;
                            border-radius: 8px;
                            margin-bottom: 0.5rem;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        '>
                            <h4 style='margin: 0 0 0.5rem 0;'>{task['title']}</h4>
                            <p style='margin: 0 0 0.75rem 0; color: #666;'>
                                {task['description'] if task['description'] else 'No description'}
                            </p>
                            <div style='color: #888; font-size: 0.9em;'>Created: {task['created_at'].strftime('%Y-%m-%d %H:%M')}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Display attachments
                    attachments = get_task_attachments(task['id'])
                    if attachments:
                        st.write("📎 Attachments:")
                        for attachment in attachments:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                with open(attachment['file_path'], 'rb') as f:
                                    st.download_button(
                                        f"📄 {attachment['filename']}",
                                        f,
                                        file_name=attachment['filename'],
                                        mime=attachment['file_type']
                                    )
                            with col2:
                                if st.button("🗑️", key=f"delete_{attachment['id']}"):
                                    if delete_attachment(attachment['id']):
                                        st.rerun()
        else:
            st.info(f"No tasks in {status}")
