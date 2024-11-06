from database.connection import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    try:
        # Read migration file
        with open('database/migrations/09_add_task_dependencies.sql', 'r') as f:
            sql = f.read()
            
        # Execute migration
        execute_query(sql)
        logger.info("Task dependencies and subtasks tables created successfully")
        
        # Verify tables were created
        tables = execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('task_dependencies', 'subtasks')
        """)
        
        if len(tables) == 2:
            logger.info("Migration verification successful")
            return True
        else:
            logger.error("Migration verification failed - tables not found")
            return False
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    apply_migration()
