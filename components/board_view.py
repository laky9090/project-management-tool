import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file, get_task_attachments
from components.board_templates import render_template_manager, get_board_templates, DEFAULT_TEMPLATES, apply_template_to_project
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    try:
        st.write("### Project Board")
        
        # Add template selection
        st.sidebar.write("### Board Template")
        all_templates = {**DEFAULT_TEMPLATES, **get_board_templates()}
        selected_template = st.sidebar.selectbox(
            "Select Template",
            options=list(all_templates.keys()),
            key="board_template"
        )
        
        if st.sidebar.button("Apply Template"):
            if apply_template_to_project(project_id, all_templates[selected_template]):
                st.success(f"Applied template: {selected_template}")
                st.rerun()
            else:
                st.error("Failed to apply template")
        
        # Template management section
        with st.sidebar.expander("Manage Templates"):
            render_template_manager()
        
        # Simple task form at the top
        with st.form("minimal_task_form"):
            st.write("Add Task")
            title = st.text_input("Title")
            description = st.text_area("Description")
            
            # Add status selection based on template
            status = st.selectbox(
                "Status",
                options=all_templates[selected_template]
            )
            
            # Add file upload field
            uploaded_file = st.file_uploader(
                "Attach File (optional)",
                type=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx']
            )
            
            if st.form_submit_button("Create Task"):
                if title:
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id, title;
                    ''', (project_id, title, description, status))
                    
                    if result:
                        task_id = result[0]['id']
                        
                        # Handle file upload if present
                        if uploaded_file:
                            file_id = save_uploaded_file(uploaded_file, task_id)
                            if file_id:
                                st.success(f"File '{uploaded_file.name}' attached successfully!")
                        
                        st.success(f"Task created: {result[0]['title']}")
                        st.rerun()
        
        # Display tasks grouped by status
        columns = st.columns(len(all_templates[selected_template]))
        tasks = execute_query('''
            SELECT id, title, description, status, created_at
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
            for col, status in zip(columns, all_templates[selected_template]):
                with col:
                    st.write(f"### {status}")
                    for task in tasks_by_status.get(status, []):
                        with st.container():
                            st.write(f"**{task['title']}**")
                            if task['description']:
                                st.write(task['description'])
                            
                            # Show attachments if any
                            attachments = get_task_attachments(task['id'])
                            if attachments:
                                st.write("📎 Attachments:")
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
            st.info("No tasks found")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        st.error(f"Error: {str(e)}")
