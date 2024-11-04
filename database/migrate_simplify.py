import streamlit as st
from database.connection import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    try:
        # Drop user-related tables
        execute_query("DROP TABLE IF EXISTS user_roles CASCADE")
        execute_query("DROP TABLE IF EXISTS roles CASCADE")
        execute_query("DROP TABLE IF EXISTS project_members CASCADE")
        execute_query("DROP TABLE IF EXISTS users CASCADE")
        
        # Modify tasks table
        execute_query("ALTER TABLE tasks DROP COLUMN IF EXISTS assignee_id")
        execute_query("ALTER TABLE tasks DROP COLUMN IF EXISTS creator_id")
        
        # Modify projects table
        execute_query("ALTER TABLE projects DROP COLUMN IF EXISTS owner_id")
        
        # Create file_attachments table if it doesn't exist
        execute_query("""
            CREATE TABLE IF NOT EXISTS file_attachments (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(255) NOT NULL,
                file_type VARCHAR(100),
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        st.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    apply_migration()
