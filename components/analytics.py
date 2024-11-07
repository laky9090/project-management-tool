import streamlit as st
from database.connection import execute_query
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

@st.cache_data(ttl=300)
def get_project_metrics(project_id):
    """Get all project metrics in a single query"""
    try:
        result = execute_query("""
            WITH task_metrics AS (
                SELECT 
                    COUNT(*) as total_tasks,
                    COUNT(*) FILTER (WHERE status = 'Done') as completed_tasks,
                    COUNT(*) FILTER (WHERE priority = 'High') as high_priority,
                    COUNT(*) FILTER (WHERE status != 'Done' AND priority = 'High') as pending_high_priority,
                    json_object_agg(status, status_count) as status_distribution,
                    json_object_agg(priority, priority_count) as priority_distribution
                FROM (
                    SELECT 
                        status,
                        priority,
                        COUNT(*) FILTER (WHERE status = tasks.status) as status_count,
                        COUNT(*) FILTER (WHERE priority = tasks.priority) as priority_count
                    FROM tasks
                    WHERE project_id = %s AND deleted_at IS NULL
                    GROUP BY status, priority
                ) t
            ),
            task_age AS (
                SELECT 
                    status,
                    AVG(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at))/86400) as avg_age_days
                FROM tasks
                WHERE project_id = %s AND deleted_at IS NULL
                GROUP BY status
            ),
            completion_trend AS (
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) FILTER (WHERE status = 'Done') as completed,
                    COUNT(*) as total
                FROM tasks
                WHERE project_id = %s AND deleted_at IS NULL
                GROUP BY DATE(created_at)
                ORDER BY date
            )
            SELECT 
                tm.*,
                json_agg(ta.*) as age_analysis,
                json_agg(ct.*) as completion_trend
            FROM task_metrics tm
            CROSS JOIN LATERAL (SELECT * FROM task_age) ta
            CROSS JOIN LATERAL (SELECT * FROM completion_trend) ct
            GROUP BY tm.total_tasks, tm.completed_tasks, tm.high_priority, 
                     tm.pending_high_priority, tm.status_distribution, tm.priority_distribution
        """, (project_id, project_id, project_id))
        
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting project metrics: {str(e)}")
        return None

def render_analytics(project_id):
    """Render analytics dashboard with optimized loading"""
    st.write("## Project Analytics")
    
    # Load all metrics at once
    metrics = get_project_metrics(project_id)
    if not metrics:
        st.error("Failed to load project metrics")
        return
    
    # Project Progress Overview
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tasks", metrics['total_tasks'])
        with col2:
            completion_rate = round((metrics['completed_tasks'] / metrics['total_tasks'] * 100 
                                   if metrics['total_tasks'] > 0 else 0), 1)
            st.metric("Completion Rate", f"{completion_rate}%")
        with col3:
            st.metric("High Priority Tasks", metrics['high_priority'])
        with col4:
            st.metric("Pending High Priority", metrics['pending_high_priority'])
    
    # Status Distribution Chart
    with st.container():
        status_dist = pd.DataFrame([
            {'status': k, 'count': v} 
            for k, v in metrics['status_distribution'].items()
        ])
        if not status_dist.empty:
            fig_status = px.pie(status_dist, values='count', names='status', 
                              title='Task Status Distribution')
            st.plotly_chart(fig_status, use_container_width=True)
    
    # Priority Distribution Chart
    with st.container():
        priority_dist = pd.DataFrame([
            {'priority': k, 'count': v} 
            for k, v in metrics['priority_distribution'].items()
        ])
        if not priority_dist.empty:
            fig_priority = px.bar(priority_dist, x='priority', y='count', 
                                title='Tasks by Priority')
            st.plotly_chart(fig_priority, use_container_width=True)
    
    # Task Completion Trend
    if metrics['completion_trend']:
        with st.container():
            df_trend = pd.DataFrame(metrics['completion_trend'])
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=df_trend['date'], y=df_trend['total'], 
                                         name='Total Tasks', mode='lines+markers'))
            fig_trend.add_trace(go.Scatter(x=df_trend['date'], y=df_trend['completed'], 
                                         name='Completed Tasks', mode='lines+markers'))
            fig_trend.update_layout(title='Task Completion Trend', 
                                  xaxis_title='Date', yaxis_title='Number of Tasks')
            st.plotly_chart(fig_trend, use_container_width=True)
    
    # Lazy load detailed analytics
    if st.checkbox("📊 Show Detailed Analytics"):
        with st.container():
            st.write("### Task Age Analysis")
            if metrics['age_analysis']:
                df_age = pd.DataFrame(metrics['age_analysis'])
                df_age['avg_age_days'] = df_age['avg_age_days'].round(1)
                fig_age = px.bar(df_age, x='status', y='avg_age_days',
                                title='Average Task Age by Status (Days)',
                                labels={'avg_age_days': 'Average Age (Days)'})
                st.plotly_chart(fig_age, use_container_width=True)
