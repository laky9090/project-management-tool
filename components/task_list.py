import streamlit as st
import pandas as pd
from database.connection import execute_query

def render_task_list(project_id):
    st.write("## Task List")
    
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
        
        # Display filtered dataframe
        st.dataframe(
            df[['title', 'status', 'priority', 'assignee', 'due_date']],
            use_container_width=True
        )
    else:
        st.info("No tasks found. Create some tasks to see them listed here.")
