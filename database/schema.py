from database.connection import execute_query
import logging

logger = logging.getLogger(__name__)

def init_database():
    try:
        # Drop existing tables
        execute_query("DROP TABLE IF EXISTS file_attachments CASCADE")
        execute_query("DROP TABLE IF EXISTS tasks CASCADE")
        execute_query("DROP TABLE IF EXISTS projects CASCADE")
        
        # Create projects table with minimal structure
        execute_query('''
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                deadline DATE
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
                priority VARCHAR(20) DEFAULT 'Medium',
                due_date DATE
            )
        ''')
        
        # Create file_attachments table
        execute_query('''
            CREATE TABLE IF NOT EXISTS file_attachments (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(255) NOT NULL,
                file_type VARCHAR(100),
                file_size INTEGER
            )
        ''')
        
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise e
