import streamlit as st
from database.connection import execute_query

def init_database():
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
            project_id INTEGER REFERENCES projects(id),
            title VARCHAR(100) NOT NULL,
            description TEXT,
            status VARCHAR(50) DEFAULT 'To Do',
            priority VARCHAR(20) DEFAULT 'Medium',
            assignee VARCHAR(100),
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
