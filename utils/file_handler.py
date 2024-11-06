import os
import uuid
import streamlit as st
from database.connection import execute_query
import logging
import mimetypes

logger = logging.getLogger(__name__)

def save_uploaded_file(uploaded_file, task_id):
    """Save an uploaded file and create a database record."""
    try:
        if uploaded_file is None:
            return None
            
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename while preserving extension
        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Get MIME type
        file_type = uploaded_file.type
        if not file_type:
            file_type = mimetypes.guess_type(uploaded_file.name)[0]
        
        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        # Create database record
        result = execute_query(
            """
            INSERT INTO file_attachments 
                (task_id, filename, file_path, file_type, file_size) 
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING id
            """,
            (task_id, uploaded_file.name, file_path, file_type, uploaded_file.size)
        )
        
        if result:
            logger.info(f"File saved successfully: {file_path}")
            return result[0]['id']
        return None
        
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        # Cleanup on failure
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return None

def get_task_attachments(task_id):
    """Get all attachments for a task."""
    try:
        attachments = execute_query("""
            SELECT id, filename, file_path, file_type, file_size, created_at
            FROM file_attachments
            WHERE task_id = %s
            ORDER BY created_at DESC
        """, (task_id,))
        
        # Verify file existence and update list accordingly
        valid_attachments = []
        for attachment in attachments:
            if os.path.exists(attachment['file_path']):
                valid_attachments.append(attachment)
            else:
                logger.warning(f"File not found: {attachment['file_path']}")
                execute_query("DELETE FROM file_attachments WHERE id = %s", (attachment['id'],))
        
        return valid_attachments
    except Exception as e:
        logger.error(f"Error fetching attachments: {str(e)}")
        return []
