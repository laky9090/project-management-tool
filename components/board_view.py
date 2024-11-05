import streamlit as st
from database.connection import execute_query
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    try:
        st.write(f"### Project {project_id} Board")
        
        # Get all tasks for this project with detailed debug info
        st.write("### Debug Information")
        st.write(f"Querying tasks for project {project_id}")
        
        # Get total task count first
        count_result = execute_query('''
            SELECT COUNT(*) as count FROM tasks WHERE project_id = %s
        ''', (project_id,))
        
        if count_result:
            st.write(f"Total tasks in project: {count_result[0]['count']}")
        
        # Create columns for each status
        cols = st.columns(3)
        
        # Display tasks by status
        for idx, status in enumerate(["To Do", "In Progress", "Done"]):
            with cols[idx]:
                st.subheader(status)
                tasks = execute_query('''
                    SELECT id, title, description, status, created_at
                    FROM tasks 
                    WHERE project_id = %s AND status = %s
                    ORDER BY created_at DESC
                ''', (project_id, status))
                
                st.write(f"Found {len(tasks) if tasks else 0} tasks in {status}")
                
                if tasks:
                    for task in tasks:
                        with st.container():
                            st.markdown(f'''
                                <div style="
                                    border: 1px solid #ddd;
                                    border-radius: 5px;
                                    padding: 10px;
                                    margin-bottom: 10px;
                                ">
                                    <h4 style="margin: 0">{task['title']}</h4>
                                    <p>{task['description'] if task['description'] else ''}</p>
                                    <small>Created: {task['created_at'].strftime('%Y-%m-%d %H:%M')}</small>
                                </div>
                            ''', unsafe_allow_html=True)
                else:
                    st.info(f"No tasks in {status}")
                    
    except Exception as e:
        st.error(f"Error rendering board: {str(e)}")
        logger.error(f"Board render error: {str(e)}")
