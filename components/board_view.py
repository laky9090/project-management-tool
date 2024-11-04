import streamlit as st
from database.connection import execute_query

def render_board(project_id):
    st.write("## Kanban Board")
    
    cols = st.columns(3)
    statuses = ["To Do", "In Progress", "Done"]
    
    for idx, status in enumerate(statuses):
        with cols[idx]:
            st.write(f"### {status}")
            tasks = execute_query("""
                SELECT * FROM tasks 
                WHERE project_id = %s AND status = %s 
                ORDER BY priority DESC
            """, (project_id, status))
            
            if tasks:
                for task in tasks:
                    with st.container():
                        st.markdown(f"""
                        <div style='padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin: 5px 0;'>
                            <h4>{task['title']}</h4>
                            <p>{task['description'][:100]}...</p>
                            <p><strong>Priority:</strong> {task['priority']}</p>
                            <p><strong>Assignee:</strong> {task['assignee']}</p>
                            <p><strong>Due:</strong> {task['due_date']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        new_status = st.selectbox(
                            "Move to",
                            statuses,
                            key=f"move_{task['id']}",
                            index=statuses.index(status)
                        )
                        
                        if new_status != status:
                            execute_query(
                                "UPDATE tasks SET status = %s WHERE id = %s",
                                (new_status, task['id'])
                            )
                            st.rerun()
