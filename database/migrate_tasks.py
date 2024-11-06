from database.connection import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_task_dependencies_migration():
    try:
        # Create task_dependencies table
        execute_query("""
            CREATE TABLE IF NOT EXISTS task_dependencies (
                id SERIAL PRIMARY KEY,
                task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                depends_on_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(task_id, depends_on_id),
                CHECK (task_id != depends_on_id)
            )
        """)
        
        # Create subtasks table
        execute_query("""
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
        """)
        
        # Add trigger for updating subtask timestamps
        execute_query("""
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
        """)
        
        logger.info("Task dependencies and subtasks migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    apply_task_dependencies_migration()
