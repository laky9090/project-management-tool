import streamlit as st
from database.connection import execute_query

def init_database():
    try:
        st.info("Initializing database tables...")
        
        # Create users table
        execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create roles table
        execute_query("""
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create user_roles junction table
        execute_query("""
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, role_id)
            )
        """)
        
        # Create projects table
        execute_query("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                deadline DATE,
                owner_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create project_members table
        execute_query("""
            CREATE TABLE IF NOT EXISTS project_members (
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                role VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (project_id, user_id)
            )
        """)
        
        # Create tasks table with ownership
        execute_query("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'To Do',
                priority VARCHAR(20) DEFAULT 'Medium',
                assignee_id INTEGER REFERENCES users(id),
                creator_id INTEGER REFERENCES users(id),
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default roles if they don't exist
        execute_query("""
            INSERT INTO roles (name, description)
            VALUES 
                ('admin', 'Full system access'),
                ('project_manager', 'Can manage projects and team members'),
                ('team_member', 'Can view and update assigned tasks')
            ON CONFLICT (name) DO NOTHING
        """)
        
        st.success("Database tables initialized successfully!")
        
    except Exception as e:
        st.error(f"Failed to initialize database tables: {str(e)}")
        raise e
