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
        <span>
            <span class="priority-indicator {priority_class}"></span>
            {priority}
        </span>
    """

def format_date(date):
    if pd.isna(date):
        return ""
    return date.strftime("%b %d, %Y")

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
        
        # Add row numbers
        df.index = range(1, len(df) + 1)
        
        # Format the data
        df['status'] = df['status'].apply(format_status)
        df['priority'] = df['priority'].apply(format_priority)
        df['due_date'] = df['due_date'].apply(format_date)
        
        # Create the styled table
        st.markdown("""
            <style>
                .dataframe {
                    font-family: 'Inter', sans-serif !important;
                }
                .dataframe td {
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Display the table with custom styling
        st.markdown(
            df[['title', 'status', 'priority', 'assignee', 'due_date']].to_html(
                escape=False,
                index=True,
                classes=['modern-table'],
                table_id='task-table'
            ),
            unsafe_allow_html=True
        )
        
        # Add JavaScript for sorting
        st.markdown("""
            <script>
                const table = document.getElementById('task-table');
                const headers = table.getElementsByTagName('th');
                
                for (let i = 0; i < headers.length; i++) {
                    headers[i].addEventListener('click', () => {
                        const column = headers[i].textContent.toLowerCase();
                        sortTable(i, column);
                    });
                }
                
                function sortTable(column, columnName) {
                    const tbody = table.getElementsByTagName('tbody')[0];
                    const rows = Array.from(tbody.getElementsByTagName('tr'));
                    
                    const sortedRows = rows.sort((a, b) => {
                        const aVal = a.getElementsByTagName('td')[column].textContent;
                        const bVal = b.getElementsByTagName('td')[column].textContent;
                        return aVal.localeCompare(bVal);
                    });
                    
                    tbody.innerHTML = '';
                    sortedRows.forEach(row => tbody.appendChild(row));
                }
            </script>
        """, unsafe_allow_html=True)
        
    else:
        st.info("No tasks found. Create some tasks to see them listed here.")
