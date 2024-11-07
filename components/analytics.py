import streamlit as st
from database.connection import execute_query
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@st.cache_data(ttl=300)
def get_task_status_distribution(project_id):
    """Get distribution of tasks by status"""
    try:
        result = execute_query("""
            SELECT status, COUNT(*) as count
            FROM tasks
            WHERE project_id = %s
            GROUP BY status
            ORDER BY count DESC
        """, (project_id,))
        return result if result else []
    except Exception as e:
        logger.error(f"Error getting task status distribution: {str(e)}")
        return []

@st.cache_data(ttl=300)
def get_priority_distribution(project_id):
    """Get distribution of tasks by priority"""
    try:
        result = execute_query("""
            SELECT priority, COUNT(*) as count
            FROM tasks
            WHERE project_id = %s
            GROUP BY priority
            ORDER BY count DESC
        """, (project_id,))
        return result if result else []
    except Exception as e:
        logger.error(f"Error getting priority distribution: {str(e)}")
        return []

@st.cache_data(ttl=300)
def get_task_completion_trend(project_id):
    """Get task completion trend over time"""
    try:
        result = execute_query("""
            SELECT DATE(created_at) as date,
                   COUNT(*) FILTER (WHERE status = 'Done') as completed,
                   COUNT(*) as total
            FROM tasks
            WHERE project_id = %s
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (project_id,))
        return result if result else []
    except Exception as e:
        logger.error(f"Error getting task completion trend: {str(e)}")
        return []

@st.cache_data(ttl=300)
def get_project_progress(project_id):
    """Get overall project progress metrics"""
    try:
        result = execute_query("""
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(*) FILTER (WHERE status = 'Done') as completed_tasks,
                COUNT(*) FILTER (WHERE priority = 'High') as high_priority,
                COUNT(*) FILTER (WHERE status != 'Done' AND priority = 'High') as pending_high_priority
            FROM tasks
            WHERE project_id = %s
        """, (project_id,))
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting project progress: {str(e)}")
        return None

def render_analytics(project_id):
    """Render analytics dashboard for a project"""
    st.write("## Project Analytics")
    
    # Use container to prevent unnecessary reruns
    with st.container():
        # Project Progress Overview
        progress = get_project_progress(project_id)
        if progress:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Tasks", progress['total_tasks'])
            with col2:
                completion_rate = round((progress['completed_tasks'] / progress['total_tasks'] * 100 if progress['total_tasks'] > 0 else 0), 1)
                st.metric("Completion Rate", f"{completion_rate}%")
            with col3:
                st.metric("High Priority Tasks", progress['high_priority'])
            with col4:
                st.metric("Pending High Priority", progress['pending_high_priority'])

    # Status Distribution Chart
    with st.container():
        status_dist = get_task_status_distribution(project_id)
        if status_dist:
            df_status = pd.DataFrame(status_dist)
            fig_status = px.pie(df_status, values='count', names='status', title='Task Status Distribution')
            st.plotly_chart(fig_status, use_container_width=True)

    # Priority Distribution Chart
    with st.container():
        priority_dist = get_priority_distribution(project_id)
        if priority_dist:
            df_priority = pd.DataFrame(priority_dist)
            fig_priority = px.bar(df_priority, x='priority', y='count', title='Tasks by Priority')
            st.plotly_chart(fig_priority, use_container_width=True)

    # Task Completion Trend
    with st.container():
        completion_trend = get_task_completion_trend(project_id)
        if completion_trend:
            df_trend = pd.DataFrame(completion_trend)
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=df_trend['date'], y=df_trend['total'], 
                                       name='Total Tasks', mode='lines+markers'))
            fig_trend.add_trace(go.Scatter(x=df_trend['date'], y=df_trend['completed'], 
                                       name='Completed Tasks', mode='lines+markers'))
            fig_trend.update_layout(title='Task Completion Trend', xaxis_title='Date', yaxis_title='Number of Tasks')
            st.plotly_chart(fig_trend, use_container_width=True)

    # Additional Analytics with lazy loading
    if st.checkbox("📊 Show Detailed Analytics"):
        with st.container():
            st.write("### Task Age Analysis")
            age_data = execute_query("""
                SELECT 
                    status,
                    AVG(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at))/86400) as avg_age_days
                FROM tasks
                WHERE project_id = %s
                GROUP BY status
            """, (project_id,))
            
            if age_data:
                df_age = pd.DataFrame(age_data)
                df_age['avg_age_days'] = df_age['avg_age_days'].round(1)
                fig_age = px.bar(df_age, x='status', y='avg_age_days', 
                               title='Average Task Age by Status (Days)',
                               labels={'avg_age_days': 'Average Age (Days)'})
                st.plotly_chart(fig_age, use_container_width=True)
