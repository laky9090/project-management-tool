import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file, get_task_attachments
import logging

logger = logging.getLogger(__name__)

def render_board(project_id):
    try:
        st.write("### Project Board")
        
        # Simple task form at the top
        with st.form("minimal_task_form"):
            st.write("Add Task")
            title = st.text_input("Title")
            description = st.text_area("Description")
            
            # Add file upload field
            uploaded_file = st.file_uploader(
                "Attach File (optional)",
                type=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx']
            )
            
            if st.form_submit_button("Create Task"):
                if title:
                    # Debug info
                    st.write("Creating task with:", {
                        "title": title,
                        "description": description,
                        "has_attachment": uploaded_file is not None
                    })
                    
                    result = execute_query('''
                        INSERT INTO tasks (project_id, title, description, status)
                        VALUES (%s, %s, %s, 'To Do')
                        RETURNING id, title;
                    ''', (project_id, title, description))
                    
                    if result:
                        task_id = result[0]['id']
                        
                        # Handle file upload if present
                        if uploaded_file:
                            file_id = save_uploaded_file(uploaded_file, task_id)
                            if file_id:
                                st.success(f"File '{uploaded_file.name}' attached successfully!")
                        
                        st.success(f"Task created: {result[0]['title']}")
                        st.rerun()
        
        # Debug section
        st.write("### Debug Information")
        tasks = execute_query('''
            SELECT id, title, description, status, created_at
            FROM tasks 
            WHERE project_id = %s
            ORDER BY created_at DESC
        ''', (project_id,))
        
        st.write(f"Found {len(tasks) if tasks else 0} tasks")
        
        # Simple task list with attachments
        if tasks:
            for task in tasks:
                st.write("---")
                st.write(f"**{task['title']}**")
                if task['description']:
                    st.write(task['description'])
                st.write(f"Created: {task['created_at']}")
                
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
