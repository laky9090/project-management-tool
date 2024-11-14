import streamlit as st
import pandas as pd
from database.connection import execute_query
from datetime import datetime

def format_status(status):
    status_class = status.lower().replace(" ", "")
    return f"""
        <span class="status-badge {status_class}">
            {status}
        </span>
    """

def format_priority(priority):
    priority_class = priority.lower()
    return f"""
        <span class="priority-indicator {priority_class}">
            {priority}
        </span>
    """

def format_date(date):
    if pd.isna(date):
        return ""
    return date.strftime("%d/%m/%Y")

def render_task_list(project_id):
    st.write("## Task List")
    
    # Get tasks from database
    tasks = execute_query("""
        SELECT * FROM tasks 
        WHERE project_id = %s 
        ORDER BY due_date
    """, (project_id,))
    
    if tasks:
        df = pd.DataFrame(tasks)
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=df['status'].unique()
            )
        with col2:
            priority_filter = st.multiselect(
                "Filter by Priority",
                options=df['priority'].unique()
            )
        
        # Apply filters
        if status_filter:
            df = df[df['status'].isin(status_filter)]
        if priority_filter:
            df = df[df['priority'].isin(priority_filter)]
        
        # Format the data
        df['status'] = df['status'].apply(format_status)
        df['priority'] = df['priority'].apply(format_priority)
        df['due_date'] = df['due_date'].apply(format_date)
        
        # Add custom CSS for table alignment
        st.markdown("""
            <style>
                .task-list-table td, .task-list-table th {
                    text-align: center !important;
                    vertical-align: middle !important;
                }
                .task-list-table td:first-child,
                .task-list-table th:first-child,
                .task-list-table td:nth-child(2),
                .task-list-table th:nth-child(2) {
                    text-align: left !important;
                }
                .task-list-container {
                    overflow-x: auto;
                    margin: 1rem 0;
                }
                .status-badge, .priority-indicator {
                    display: inline-flex;
                    justify-content: center;
                    align-items: center;
                    margin: 0 auto;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Display the table
        st.markdown(
            df[['title', 'status', 'priority', 'assignee', 'due_date']].to_html(
                escape=False,
                index=True,
                classes=['task-list-table'],
                table_id='task-table'
            ),
            unsafe_allow_html=True
        )
        
    else:
        st.info("No tasks found. Create some tasks to see them listed here.")