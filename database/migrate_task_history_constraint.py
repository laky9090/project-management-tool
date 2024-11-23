from database.connection import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    try:
        # Read and execute migration file
        with open('database/migrations/16_update_task_history_constraint.sql', 'r') as f:
            migration_sql = f.read()
            
        execute_query(migration_sql)
        logger.info("Updated task_history foreign key constraint successfully")
        
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    apply_migration()
