import streamlit as st
from database.connection import execute_query

def get_priority_class(priority):
    return f"priority-{priority.lower()}"

def get_status_class(status):
    status_map = {
        "To Do": "todo",
        "In Progress": "progress",
        "Done": "done"
    }
    return f"status-{status_map[status]}"

def render_board(project_id):
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
            
            tasks = execute_query("""
                SELECT * FROM tasks 
                WHERE project_id = %s AND status = %s 
                ORDER BY priority DESC
            """, (project_id, status))
            
            if tasks:
                for task in tasks:
                    priority_class = get_priority_class(task['priority'])
                    status_class = get_status_class(status)
                    
                    with st.container():
                        st.markdown(f"""
                        <div class='task-card {status_class}' style='
                            background: white;
                            border-radius: 12px;
                            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                            margin: 0.75rem 0;
                            overflow: hidden;
                        '>
                            <div class='{priority_class}' style='
                                padding: 0.5rem 1rem;
                                font-weight: 500;
                                font-size: 0.875rem;
                                margin-bottom: 0.5rem;
                            '>
                                {task['priority']} Priority
                            </div>
                            <div style='padding: 1rem;'>
                                <h4 style='
                                    margin: 0 0 0.5rem 0;
                                    font-size: 1rem;
                                    font-weight: 600;
                                    color: #1F2937;
                                '>{task['title']}</h4>
                                <p style='
                                    margin: 0 0 0.75rem 0;
                                    color: #6B7280;
                                    font-size: 0.875rem;
                                '>{task['description'][:100]}...</p>
                                <div style='
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    font-size: 0.875rem;
                                    color: #4B5563;
                                '>
                                    <span>👤 {task['assignee']}</span>
                                    <span>📅 {task['due_date']}</span>
                                </div>
                            </div>
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
