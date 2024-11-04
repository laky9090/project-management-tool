import os
import uuid
import streamlit as st
from database.connection import execute_query

def save_uploaded_file(uploaded_file, task_id):
    try:
        if uploaded_file is None:
            return None

        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Save file information to database
        result = execute_query("""
            INSERT INTO file_attachments 
                (task_id, filename, file_path, file_type, file_size)
            VALUES 
                (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            task_id,
            uploaded_file.name,
            file_path,
            uploaded_file.type,
            uploaded_file.size
        ))

        if result:
            return result[0]['id']
        return None

    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return None

def get_task_attachments(task_id):
    try:
        return execute_query("""
            SELECT id, filename, file_path, file_type, file_size, created_at
            FROM file_attachments
            WHERE task_id = %s
            ORDER BY created_at DESC
        """, (task_id,))
    except Exception as e:
        st.error(f"Error fetching attachments: {str(e)}")
        return []

def delete_attachment(attachment_id):
    try:
        # Get file path before deletion
        result = execute_query("""
            SELECT file_path FROM file_attachments
            WHERE id = %s
        """, (attachment_id,))

        if result:
            file_path = result[0]['file_path']
            
            # Delete from database
            execute_query("""
                DELETE FROM file_attachments
                WHERE id = %s
            """, (attachment_id,))

            # Delete physical file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return True
        return False
    except Exception as e:
        st.error(f"Error deleting attachment: {str(e)}")
        return False