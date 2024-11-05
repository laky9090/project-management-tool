from database.connection import execute_query
import logging
import os

logger = logging.getLogger(__name__)

def init_database():
    try:
        # Create projects table with minimal structure
        execute_query('''
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                deadline DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create tasks table with minimal structure
        execute_query('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'To Do',
                priority VARCHAR(50) DEFAULT 'Medium',
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Add priority column if it doesn't exist
            DO $$ 
            BEGIN 
                IF NOT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'tasks' AND column_name = 'priority'
                ) THEN
                    ALTER TABLE tasks ADD COLUMN priority VARCHAR(50) DEFAULT 'Medium';
                END IF;
            END $$;
        ''')
        
        # Create file_attachments table
        execute_query('''
            CREATE TABLE IF NOT EXISTS file_attachments (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(255) NOT NULL,
                file_type VARCHAR(100),
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create uploads directory if it doesn't exist
        os.makedirs('uploads', exist_ok=True)
        
        logger.info("Database schema initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
