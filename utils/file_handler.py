import os
import uuid
import streamlit as st
from database.connection import execute_query
import logging

logger = logging.getLogger(__name__)

def save_uploaded_file(uploaded_file, task_id, cursor=None):
    try:
        if uploaded_file is None:
            return None
            
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        result = execute_query(
            "INSERT INTO file_attachments (task_id, filename, file_path, file_type, file_size) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (task_id, uploaded_file.name, file_path, uploaded_file.type, uploaded_file.size)
        )
        
        if result:
            logger.info(f"File saved: {file_path}")
            return result[0]['id']
        return None
        
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return None

def get_task_attachments(task_id):
    """Get all attachments for a task."""
    try:
        return execute_query("""
            SELECT id, filename, file_path, file_type, file_size, created_at
            FROM file_attachments
            WHERE task_id = %s
            ORDER BY created_at DESC
        """, (task_id,))
    except Exception as e:
        logger.error(f"Error fetching attachments: {str(e)}")
        return []
