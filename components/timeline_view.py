import streamlit as st
import plotly.figure_factory as ff
from database.connection import execute_query
from datetime import datetime

def render_timeline(project_id):
    st.write("## Project Timeline")
    
    tasks = execute_query("""
        SELECT title, due_date, status, priority 
        FROM tasks 
        WHERE project_id = %s 
        ORDER BY due_date
    """, (project_id,))
    
    if tasks:
        df = []
        colors = {'To Do': 'rgb(220, 0, 0)', 
                 'In Progress': 'rgb(255, 165, 0)', 
                 'Done': 'rgb(0, 255, 0)'}
        
        for task in tasks:
            df.append(dict(
                Task=task['title'],
                Start=datetime.now().date(),
                Finish=task['due_date'],
                Status=task['status']
            ))
        
        fig = ff.create_gantt(
            df,
            colors=colors,
            index_col='Status',
            show_colorbar=True,
            group_tasks=True,
            showgrid_x=True,
            showgrid_y=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tasks found for timeline visualization.")
