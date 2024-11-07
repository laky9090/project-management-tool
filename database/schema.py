from database.connection import execute_query
import logging
import os

logger = logging.getLogger(__name__)

def init_database():
    try:
        # Create projects table
        execute_query('''
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                deadline DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            )
        ''')
        
        # Add deleted_at column to projects table if it doesn't exist
        execute_query('''
            ALTER TABLE projects 
            ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
        ''')
        
        # Create tasks table
        execute_query('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'To Do',
                priority VARCHAR(50) DEFAULT 'Medium',
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            )
        ''')
        
        # Create task_dependencies table
        execute_query('''
            CREATE TABLE IF NOT EXISTS task_dependencies (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                depends_on_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(task_id, depends_on_id),
                CHECK (task_id != depends_on_id)
            )
        ''')
        
        # Create subtasks table
        execute_query('''
            CREATE TABLE IF NOT EXISTS subtasks (
                id SERIAL PRIMARY KEY,
                parent_task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'To Do',
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create trigger for updating subtasks timestamp
        execute_query('''
            CREATE OR REPLACE FUNCTION update_subtask_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';

            DROP TRIGGER IF EXISTS update_subtask_timestamp ON subtasks;
            
            CREATE TRIGGER update_subtask_timestamp
                BEFORE UPDATE ON subtasks
                FOR EACH ROW
                EXECUTE FUNCTION update_subtask_timestamp();
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

        # Create board_templates table
        execute_query('''
            CREATE TABLE IF NOT EXISTS board_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                columns JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Insert default template if it doesn't exist
            INSERT INTO board_templates (name, columns) VALUES
                ('Basic Kanban', '["To Do", "In Progress", "Done"]')
            ON CONFLICT (name) DO NOTHING;
        ''')
        
        # Create uploads directory if it doesn't exist
        os.makedirs('uploads', exist_ok=True)
        
        logger.info("Database schema initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
