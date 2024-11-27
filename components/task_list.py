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
    if isinstance(date, str):
        try:
            date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return date
    
    # Check if date is past due
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    is_past_due = date < today
    
    formatted_date = date.strftime("%d/%m/%Y")
    if is_past_due:
        return f"""<span class="past-due">{formatted_date}</span>"""
    return formatted_date

def update_task(task_id, field, value):
    try:
        if field == "due_date" and value:
            try:
                # Convert date from DD/MM/YYYY to YYYY-MM-DD for database
                value = datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError as e:
                logger.error(f"Date conversion error: {str(e)}")
                return False

        # Use parameterized query for safety
        query = f"""
            UPDATE tasks 
            SET {field} = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s AND deleted_at IS NULL 
            RETURNING id
        """
        result = execute_query(query, (value, task_id))
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
        ORDER BY t.end_date
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
                    min-height: 24px;
                }
                .task-list-table td[contenteditable="true"]:hover {
                    background-color: #f1f5f9;
                }
                .task-list-table td[contenteditable="true"]:focus {
                    outline: 2px solid #3b82f6;
                    background-color: white;
                    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
                }
                .task-list-table td:nth-child(5), 
                .task-list-table td:nth-child(6),
                .task-list-table th:nth-child(5),
                .task-list-table th:nth-child(6) {
                    text-align: center !important;
                }
                .date-picker {
                    display: none;
                    position: absolute;
                    z-index: 1000;
                }
                .past-due {
                    color: red;
                    font-weight: bold;
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
        
        # Add JavaScript for handling inline editing
        st.markdown("""
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                document.querySelectorAll('.editable').forEach(cell => {
                    // Store original content on focus
                    cell.addEventListener('focus', function() {
                        this.dataset.originalContent = this.textContent;
                    });
                    
                    // Handle blur event for saving changes
                    cell.addEventListener('blur', function() {
                        const newValue = this.textContent.trim();
                        if (newValue !== this.dataset.originalContent) {
                            const taskId = this.dataset.taskId;
                            const field = this.dataset.field;
                            
                            // Send update to server
                            fetch(`/update_task/${taskId}`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    field: field,
                                    value: newValue
                                })
                            }).then(response => {
                                if (!response.ok) {
                                    this.textContent = this.dataset.originalContent;
                                    throw new Error('Failed to update task');
                                }
                            }).catch(error => {
                                console.error('Error:', error);
                                this.textContent = this.dataset.originalContent;
                            });
                        }
                    });
                    
                    // Handle date cells
                    if (cell.classList.contains('date-cell')) {
                        cell.addEventListener('click', function(e) {
                            const dateInput = document.createElement('input');
                            dateInput.type = 'date';
                            dateInput.style.position = 'absolute';
                            dateInput.style.left = e.pageX + 'px';
                            dateInput.style.top = e.pageY + 'px';
                            dateInput.style.zIndex = '1000';
                            
                            dateInput.addEventListener('change', () => {
                                const date = new Date(dateInput.value);
                                const formattedDate = date.toLocaleDateString('fr-FR');
                                this.textContent = formattedDate;
                                dateInput.remove();
                                this.dispatchEvent(new Event('blur'));
                            });
                            
                            document.body.appendChild(dateInput);
                            dateInput.click();
                        });
                    }
                });
            });
            </script>
        """, unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)
        
    else:
        st.info("No tasks found. Create some tasks to see them listed here.")