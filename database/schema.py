import streamlit as st
from database.connection import execute_query

def init_database():
    try:
        # Create projects table
        st.info("Initializing database tables...")
        execute_query("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                deadline DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create tasks table with CASCADE delete
        execute_query("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'To Do',
                priority VARCHAR(20) DEFAULT 'Medium',
                assignee VARCHAR(100),
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        st.success("Database tables initialized successfully!")
    except Exception as e:
        st.error(f"Failed to initialize database tables: {str(e)}")
        raise e
