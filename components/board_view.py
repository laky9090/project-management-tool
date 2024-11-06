import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file, get_task_attachments
from components.board_templates import get_board_templates, DEFAULT_TEMPLATES, apply_template_to_project
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    try:
        st.write("### Project Board")
        
        # Template Management Section
        with st.sidebar:
            st.write("### Board Template")
            
            # Get all templates
            all_templates = {**DEFAULT_TEMPLATES, **get_board_templates()}
            
            # Get current project's tasks to determine current template
            current_tasks = execute_query(
                "SELECT DISTINCT status FROM tasks WHERE project_id = %s",
                (project_id,)
            )
            current_statuses = [task['status'] for task in current_tasks] if current_tasks else []
            
            # Try to detect current template
            current_template = None
            for name, columns in all_templates.items():
                if set(current_statuses).issubset(set(columns)):
                    current_template = name
                    break
            
            # Template selection
            selected_template = st.selectbox(
                "Select Template",
                options=list(all_templates.keys()),
                index=list(all_templates.keys()).index(current_template) if current_template else 0,
                key="board_template"
            )
            
            # Show preview of selected template
            st.write("#### Template Preview:")
            cols = st.columns(len(all_templates[selected_template]))
            for col, status in zip(cols, all_templates[selected_template]):
                with col:
                    st.markdown(f"**{status}**")
            
            # Template application with confirmation
            if current_template and selected_template != current_template:
                st.warning(f"Switching templates will reorganize your tasks. Tasks in columns that don't exist in the new template will be moved to '{all_templates[selected_template][0]}'")
            
            if st.button("Apply Template", type="primary"):
                with st.spinner("Applying template..."):
                    if apply_template_to_project(project_id, all_templates[selected_template]):
                        st.success(f"Successfully applied template: {selected_template}")
                        st.rerun()
                    else:
                        st.error("Failed to apply template")
            
            # Link to template management
            if st.button("Manage Templates"):
                st.session_state.show_template_manager = True
                st.rerun()
        
        # Show template manager in main area if requested
        if getattr(st.session_state, 'show_template_manager', False):
            st.write("### Custom Board Templates")
            
            # Template creation form
            with st.form("new_template_form"):
                template_name = st.text_input(
                    "Template Name",
                    help="Enter a unique name for your template"
                )
                
                # Dynamic column input
                st.write("#### Define Columns")
                st.info("Enter one column name per line. Order matters - columns will appear left to right.")
                columns_input = st.text_area(
                    "Columns",
                    placeholder="To Do\nIn Progress\nDone",
                    help="Enter at least 2 columns, one per line"
                )
                
                # Preview current layout
                if columns_input:
                    columns = [col.strip() for col in columns_input.split('\n') if col.strip()]
                    if columns:
                        st.write("#### Preview:")
                        cols = st.columns(len(columns))
                        for idx, (col, column_name) in enumerate(zip(cols, columns)):
                            with col:
                                st.markdown(f"**{column_name}**")
                
                submitted = st.form_submit_button("Save Template")
                if submitted:
                    if template_name and columns_input:
                        columns = [col.strip() for col in columns_input.split('\n') if col.strip()]
                        if len(columns) < 2:
                            st.error("Template must have at least 2 columns")
                        else:
                            # Save template logic here
                            result = execute_query("""
                                INSERT INTO board_templates (name, columns)
                                VALUES (%s, %s)
                                ON CONFLICT (name) DO NOTHING
                                RETURNING id
                            """, (template_name, columns))
                            
                            if result:
                                st.success(f"Template '{template_name}' saved successfully!")
                                st.session_state.show_template_manager = False
                                st.rerun()
                            else:
                                st.error("Failed to save template. Name might already exist.")
                    else:
                        st.error("Please fill in all fields")
            
            # Back button
            if st.button("Back to Board"):
                st.session_state.show_template_manager = False
                st.rerun()
            
            return  # Don't show board when in template management mode
        
        # Task Creation Form
        with st.form("minimal_task_form"):
            st.write("Add Task")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                title = st.text_input("Title")
                description = st.text_area("Description", height=100)
            
            with col2:
                status = st.selectbox(
                    "Status",
                    options=all_templates[selected_template]
                )
                priority = st.selectbox(
                    "Priority",
                    options=["Low", "Medium", "High"]
                )
            
            uploaded_file = st.file_uploader(
                "Attach File (optional)",
                type=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx']
            )
            
            if st.form_submit_button("Create Task", type="primary"):
                if title:
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status, priority)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id, title;
                    ''', (project_id, title, description, status, priority))
                    
                    if result:
                        task_id = result[0]['id']
                        
                        # Handle file upload if present
                        if uploaded_file:
                            file_id = save_uploaded_file(uploaded_file, task_id)
                            if file_id:
                                st.success(f"✅ File '{uploaded_file.name}' attached!")
                        
                        st.success(f"✅ Task '{title}' created!")
                        st.rerun()
        
        # Display Kanban Board
        board_columns = st.columns(len(all_templates[selected_template]))
        tasks = execute_query('''
            SELECT id, title, description, status, priority, created_at
            FROM tasks 
            WHERE project_id = %s
            ORDER BY created_at DESC
        ''', (project_id,))
        
        if tasks:
            # Group tasks by status
            tasks_by_status = {}
            for status in all_templates[selected_template]:
                tasks_by_status[status] = [
                    task for task in tasks if task['status'] == status
                ]
            
            # Display tasks in columns
            for col, status in zip(board_columns, all_templates[selected_template]):
                with col:
                    st.write(f"### {status}")
                    st.write(f"({len(tasks_by_status[status])} tasks)")
                    
                    for task in tasks_by_status[status]:
                        with st.container():
                            # Task card with colored border based on priority
                            priority_colors = {
                                "Low": "#28a745",
                                "Medium": "#ffc107",
                                "High": "#dc3545"
                            }
                            priority = task.get('priority', 'Medium')
                            
                            st.markdown(f"""
                                <div style="
                                    border-left: 4px solid {priority_colors[priority]};
                                    padding: 10px;
                                    margin: 5px 0;
                                    background: white;
                                    border-radius: 4px;
                                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                                    <strong>{task['title']}</strong>
                                    <p style="margin: 5px 0; font-size: 0.9em;">{task['description']}</p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Show attachments if any
                            attachments = get_task_attachments(task['id'])
                            if attachments:
                                st.markdown("📎 Attachments:")
                                for attachment in attachments:
                                    try:
                                        with open(attachment['file_path'], 'rb') as f:
                                            st.download_button(
                                                f"📄 {attachment['filename']}", 
                                                f,
                                                file_name=attachment['filename'],
                                                mime=attachment['file_type']
                                            )
                                    except Exception as e:
                                        logger.error(f"Error loading attachment: {str(e)}")
        else:
            st.info("No tasks found. Create your first task to get started!")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        st.error(f"An error occurred while rendering the board: {str(e)}")
