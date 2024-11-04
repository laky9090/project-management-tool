import streamlit as st
from database.connection import execute_query

def init_database():
    try:
        st.info("Initializing database tables...")
        
        # Create projects table
        execute_query("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                deadline DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create tasks table
        execute_query("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'To Do',
                priority VARCHAR(20) DEFAULT 'Medium',
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create file_attachments table
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
        
        st.success("Database tables initialized successfully!")
        
    except Exception as e:
        st.error(f"Failed to initialize database tables: {str(e)}")
        raise e
