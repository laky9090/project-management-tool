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
        <div class="priority-indicator {priority_class}" data-priority="{priority}">
            {priority}
        </div>
    """

def format_date(date):
    if pd.isna(date):
        return ""
    return date.strftime("%d/%m/%Y")

def update_task(task_id, field, value):
    try:
        if field == "due_date":
            try:
                value = datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                return False

        result = execute_query(
            f"UPDATE tasks SET {field} = %s WHERE id = %s RETURNING id",
            (value, task_id)
        )
        return bool(result)
    except Exception as e:
        logger.error(f"Error updating task {field}: {str(e)}")
        return False

def render_task_list(project_id):
    st.write("## Task List")
    
    tasks = execute_query("""
        SELECT * FROM tasks 
        WHERE project_id = %s 
        ORDER BY due_date
    """, (project_id,))
    
    if tasks:
        df = pd.DataFrame(tasks)
        
        table_html = "<table class='task-list-table'><thead><tr>"
        columns = ['Title', 'Comment', 'Status', 'Priority', 'Due Date']
        for col in columns:
            align_class = "center-align" if col in ["Due Date", "Priority"] else ""
            table_html += f"<th class='{align_class}'>{col}</th>"
        table_html += "</tr></thead><tbody>"
        
        for _, row in df.iterrows():
            table_html += f"<tr data-status='{row['status'].lower()}'>"
            # Title cell
            table_html += f"""<td class='editable' data-task-id='{row["id"]}' 
                          data-field='title' contenteditable='true'>{row["title"]}</td>"""
            # Comment cell
            table_html += f"""<td class='editable' data-task-id='{row["id"]}' 
                          data-field='comment' contenteditable='true'>{row["comment"] or ""}</td>"""
            # Status cell
            table_html += f"<td>{format_status(row['status'])}</td>"
            # Priority cell with data attribute
            table_html += f"""<td class='editable' data-task-id='{row["id"]}' 
                          data-field='priority' data-priority='{row["priority"]}'>{format_priority(row["priority"])}</td>"""
            # Due Date cell
            table_html += f"""<td class='editable date-cell' data-task-id='{row["id"]}' 
                          data-field='due_date' contenteditable='true'>{format_date(row['due_date'])}</td>"""
            table_html += "</tr>"
        
        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.info("No tasks found. Create some tasks to see them listed here.")
