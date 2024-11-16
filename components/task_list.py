import streamlit as st
import pandas as pd
from database.connection import execute_query
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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

def update_task(task_id, field, value):
    try:
        if field == "due_date":
            try:
                # Convert date from DD/MM/YYYY to YYYY-MM-DD
                value = datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                return False

        result = execute_query(
            f"UPDATE tasks SET {field} = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s RETURNING id",
            (value, task_id)
        )
        return bool(result)
    except Exception as e:
        logger.error(f"Error updating task {field}: {str(e)}")
        return False

def render_task_list(project_id):
    st.write("## Task List")
    
    # Get tasks from database
    tasks = execute_query("""
        SELECT 
            t.*,
            COALESCE(t.updated_at, t.created_at) as last_update 
        FROM tasks t
        WHERE t.project_id = %s AND t.deleted_at IS NULL
        ORDER BY t.due_date
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
        df['last_update'] = df['last_update'].apply(format_date)
        
        # Create the Excel-like table container with centered date columns
        st.markdown("""
            <style>
                .task-list-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .task-list-table th, .task-list-table td {
                    padding: 8px;
                    border: 1px solid #e5e7eb;
                }
                .task-list-table td[contenteditable="true"] {
                    cursor: text;
                    background-color: #f8fafc;
                }
                .task-list-table td[contenteditable="true"]:hover {
                    background-color: #f1f5f9;
                }
                .task-list-table td[contenteditable="true"]:focus {
                    outline: 2px solid #3b82f6;
                    background-color: white;
                }
                .task-list-table td:nth-child(5), 
                .task-list-table td:nth-child(6),
                .task-list-table th:nth-child(5),
                .task-list-table th:nth-child(6) {
                    text-align: center !important;
                }
            </style>
            <div class="task-list-container">
                <div style="overflow-x: auto;">
        """, unsafe_allow_html=True)
        
        # Generate table HTML with editable cells
        table_html = "<table class='task-list-table'><thead><tr>"
        columns = ['Title', 'Comment', 'Status', 'Priority', 'Due Date', 'Last Update']
        for col in columns:
            align_class = "center-align" if col in ["Due Date", "Last Update"] else ""
            table_html += f"<th class='{align_class}'>{col}</th>"
        table_html += "</tr></thead><tbody>"
        
        for _, row in df.iterrows():
            table_html += f"<tr data-status='{row['status']}'>"
            # Title cell
            table_html += f"""<td class='editable' data-task-id='{row["id"]}' 
                          data-field='title' contenteditable='true'>{row["title"]}</td>"""
            # Comment cell
            table_html += f"""<td class='editable' data-task-id='{row["id"]}' 
                          data-field='comment' contenteditable='true'>{row["comment"] or ""}</td>"""
            # Status cell
            table_html += f"<td>{row['status']}</td>"
            # Priority cell
            table_html += f"<td>{row['priority']}</td>"
            # Due Date cell
            table_html += f"""<td class='editable date-cell' data-task-id='{row["id"]}' 
                          data-field='due_date' contenteditable='true'>{row['due_date']}</td>"""
            # Last Update cell
            table_html += f"<td>{row['last_update']}</td>"
            table_html += "</tr>"
        
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
        
    else:
        st.info("No tasks found. Create some tasks to see them listed here.")
