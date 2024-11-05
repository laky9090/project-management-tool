import streamlit as st
from database.connection import execute_query
from utils.file_handler import get_task_attachments, delete_attachment
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    try:
        logger.info(f"Rendering board for project {project_id}")
        
        # Verify project exists and has tasks
        project_check = execute_query('''
            SELECT p.id, 
                   (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) as task_count
            FROM projects p 
            WHERE p.id = %s
        ''', (project_id,))
        
        if not project_check:
            logger.error(f"Project {project_id} not found")
            st.error("Selected project not found")
            return
            
        logger.info(f"Project has {project_check[0]['task_count']} total tasks")
        
        st.write("## Kanban Board")
        
        cols = st.columns(3)
        statuses = ["To Do", "In Progress", "Done"]
        
        for idx, status in enumerate(statuses):
            with cols[idx]:
                st.subheader(status)
                
                tasks = execute_query('''
                    SELECT id, title, description, status, created_at 
                    FROM tasks 
                    WHERE project_id = %s AND status = %s
                    ORDER BY created_at DESC
                ''', (project_id, status))
                
                logger.info(f"Found {len(tasks) if tasks else 0} tasks with status '{status}'")
                
                if tasks:
                    for task in tasks:
                        with st.container():
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
                                    {task['description'][:100] + '...' if task['description'] and len(task['description']) > 100 else task['description'] or 'No description'}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Display attachments
                            attachments = get_task_attachments(task['id'])
                            if attachments:
                                st.write("📎 Attachments:")
                                for attachment in attachments:
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.download_button(
                                            f"📄 {attachment['filename']}",
                                            open(attachment['file_path'], 'rb'),
                                            file_name=attachment['filename'],
                                            mime=attachment['file_type']
                                        )
                                    with col2:
                                        if st.button("🗑️", key=f"delete_{attachment['id']}"):
                                            if delete_attachment(attachment['id']):
                                                st.rerun()
                            
                            # Task actions
                            new_status = st.selectbox(
                                "Move to",
                                statuses,
                                key=f"move_{task['id']}",
                                index=statuses.index(status)
                            )
                            
                            if new_status != status:
                                try:
                                    execute_query("BEGIN")
                                    if execute_query(
                                        "UPDATE tasks SET status = %s WHERE id = %s",
                                        (new_status, task['id'])
                                    ) is not None:
                                        execute_query("COMMIT")
                                        st.rerun()
                                    else:
                                        execute_query("ROLLBACK")
                                        st.error("Failed to update task status")
                                except Exception as e:
                                    execute_query("ROLLBACK")
                                    st.error(f"Error updating task status: {str(e)}")
                else:
                    st.info(f"No tasks in {status}")
                    
    except Exception as e:
        logger.error(f"Error rendering board: {str(e)}")
        st.error("Error loading the Kanban board")
