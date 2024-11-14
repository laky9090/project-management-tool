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
    return date.strftime("%d/%m/%Y")  # Updated date format to match DD/MM/YYYY

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
        
        # Create the Excel-like table container with centered date column
        st.markdown("""
            <style>
                .task-list-table td:nth-child(5) {
                    text-align: center !important;
                }
                .task-list-table th:nth-child(5) {
                    text-align: center !important;
                }
            </style>
            <div class="task-list-container">
                <div style="overflow-x: auto;">
        """, unsafe_allow_html=True)
        
        # Display the table with custom styling
        st.markdown(
            df[['title', 'status', 'priority', 'assignee', 'due_date']].to_html(
                escape=False,
                index=True,
                classes=['task-list-table'],
                table_id='task-table'
            ),
            unsafe_allow_html=True
        )
        
        st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Add JavaScript for sorting and column resizing
        st.markdown("""
            <script>
                // Sorting functionality
                document.querySelectorAll('#task-table th').forEach((header, index) => {
                    header.addEventListener('click', () => {
                        const table = document.getElementById('task-table');
                        const tbody = table.querySelector('tbody');
                        const rows = Array.from(tbody.querySelectorAll('tr'));
                        
                        const isAscending = header.classList.contains('asc');
                        
                        // Remove sorting classes from all headers
                        table.querySelectorAll('th').forEach(th => {
                            th.classList.remove('asc', 'desc');
                        });
                        
                        // Sort the rows
                        rows.sort((rowA, rowB) => {
                            const cellA = rowA.cells[index].textContent.trim();
                            const cellB = rowB.cells[index].textContent.trim();
                            
                            return isAscending ? 
                                cellB.localeCompare(cellA) : 
                                cellA.localeCompare(cellB);
                        });
                        
                        // Update sorting indicator
                        header.classList.toggle('desc', isAscending);
                        header.classList.toggle('asc', !isAscending);
                        
                        // Rerender the sorted rows
                        tbody.innerHTML = '';
                        rows.forEach(row => tbody.appendChild(row));
                    });
                });
                
                // Column resizing functionality
                let isResizing = false;
                let currentHeader = null;
                let startX, startWidth;
                
                document.querySelectorAll('#task-table th').forEach(header => {
                    const resizeHandle = document.createElement('div');
                    resizeHandle.className = 'resize-handle';
                    header.appendChild(resizeHandle);
                    
                    resizeHandle.addEventListener('mousedown', e => {
                        isResizing = true;
                        currentHeader = header;
                        startX = e.pageX;
                        startWidth = header.offsetWidth;
                        
                        document.addEventListener('mousemove', handleMouseMove);
                        document.addEventListener('mouseup', () => {
                            isResizing = false;
                            document.removeEventListener('mousemove', handleMouseMove);
                        });
                    });
                });
                
                function handleMouseMove(e) {
                    if (isResizing) {
                        const width = startWidth + (e.pageX - startX);
                        currentHeader.style.width = `${width}px`;
                    }
                }
            </script>
            
            <style>
                .resize-handle {
                    position: absolute;
                    right: 0;
                    top: 0;
                    bottom: 0;
                    width: 4px;
                    cursor: col-resize;
                    background: transparent;
                }
                
                .resize-handle:hover {
                    background: #e2e8f0;
                }
                
                #task-table th.asc::after {
                    content: ' ↑';
                }
                
                #task-table th.desc::after {
                    content: ' ↓';
                }
            </style>
        """, unsafe_allow_html=True)
        
    else:
        st.info("No tasks found. Create some tasks to see them listed here.")