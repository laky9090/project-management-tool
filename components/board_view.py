import streamlit as st
from database.connection import execute_query

def render_board(project_id):
    try:
        st.write(f"### Project {project_id} Board")
        
        # Get all tasks
        tasks = execute_query('SELECT * FROM tasks WHERE project_id = %s', (project_id,))
        
        st.write(f"Debug: Found {len(tasks) if tasks else 0} tasks")
        
        if tasks:
            for task in tasks:
                st.write("---")
                st.write(f"**{task['title']}**")
                st.write(f"Status: {task['status']}")
                st.write(f"Created: {task['created_at']}")
        else:
            st.info("No tasks found")
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
