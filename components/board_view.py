import streamlit as st
from database.connection import execute_query
from utils.file_handler import get_task_attachments, delete_attachment
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    try:
        # Clear task_created flag if exists
        if 'task_created' in st.session_state:
            del st.session_state.task_created
            st.rerun()
            
        logger.info(f"Rendering board for project {project_id}")
        
        # First verify project exists and has tasks
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
                st.markdown(f"""
                    <div style='
                        background: #F9FAFB;
                        padding: 1rem;
                        border-radius: 12px;
                        margin-bottom: 1rem;
                    '>
                        <h3 style='
                            color: #1F2937;
                            font-size: 1.25rem;
                            font-weight: 600;
                            margin-bottom: 1rem;
                        '>{status}</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                tasks = execute_query('''
                    SELECT t.id, t.title, t.description, t.status, t.priority,
                           t.due_date, t.created_at 
                    FROM tasks t
                    WHERE t.project_id = %s AND t.status = %s
                    ORDER BY t.priority DESC, t.created_at DESC
                ''', (project_id, status))
                
                if tasks:
                    for task in tasks:
                        with st.container():
                            st.markdown(f"""
                            <div class='task-card' style='
                                background: white;
                                border-radius: 12px;
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                                margin: 0.75rem 0;
                                padding: 1rem;
                            '>
                                <h4 style='margin: 0 0 0.5rem 0;'>{task['title']}</h4>
                                <p style='margin: 0 0 0.75rem 0; color: #6B7280;'>{task['description'][:100] + '...' if task['description'] and len(task['description']) > 100 else task['description'] or 'No description'}</p>
                                <div style='
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    font-size: 0.875rem;
                                    color: #4B5563;
                                '>
                                    <span class='priority-{task['priority'].lower()}'>{task['priority']}</span>
                                    <span>📅 {task['due_date'].strftime('%b %d') if task['due_date'] else 'No due date'}</span>
                                </div>
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
