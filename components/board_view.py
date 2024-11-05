import streamlit as st
from database.connection import execute_query
import logging
from utils.file_handler import get_task_attachments

logger = logging.getLogger(__name__)

def render_board(project_id):
    try:
        st.write(f"### Project {project_id} Board")
        
        # Force cache clear for tasks query
        tasks = execute_query('''
            SELECT * FROM tasks 
            WHERE project_id = %s
            ORDER BY created_at DESC
        ''', (project_id,), use_cache=False)
        
        st.write("### Debug Information")
        st.write(f"Querying tasks for project {project_id}")
        st.write(f"Total tasks in project: {len(tasks) if tasks else 0}")
        
        # Display tasks by status
        for status in ["To Do", "In Progress", "Done"]:
            st.subheader(status)
            status_tasks = [t for t in tasks if t['status'] == status] if tasks else []
            
            st.write(f"Found {len(status_tasks)} tasks in {status}")
            
            if status_tasks:
                for task in status_tasks:
                    with st.container():
                        # Task information
                        st.markdown(f"""
                            <div style="border: 1px solid #ddd; padding: 10px; margin: 5px 0;">
                                <h4>{task['title']}</h4>
                                <p>{task['description'] or ''}</p>
                                <small>Created: {task['created_at'].strftime('%Y-%m-%d %H:%M')}</small>
                            </div>
                        """, unsafe_allow_html=True)
                        
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
                                    logger.error(f"Error displaying attachment: {str(e)}")
                                    st.warning(f"Could not load attachment: {attachment['filename']}")
            else:
                st.info(f"No tasks in {status}")
                
    except Exception as e:
        logger.error(f"Error rendering board: {str(e)}")
        st.error(f"Error: {str(e)}")
