from database.connection import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    try:
        # Read and execute migration file
        with open('database/migrations/17_fix_task_deletion_order.sql', 'r') as f:
            migration_sql = f.read()
            
        execute_query(migration_sql)
        logger.info("Successfully fixed task deletion order and cascade constraints")
        
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    apply_migration()
