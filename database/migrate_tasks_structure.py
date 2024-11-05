from database.connection import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    try:
        # Read migration file
        with open('database/migrations/07_update_tasks_structure.sql', 'r') as f:
            sql = f.read()
            
        # Execute migration
        execute_query(sql)
        logger.info("Tasks table structure updated successfully")
        
        # Verify changes by checking table structure
        result = execute_query("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'tasks'
            ORDER BY ordinal_position;
        """)
        
        logger.info("Updated tasks table structure:")
        for col in result:
            logger.info(f"{col['column_name']}: {col['data_type']} (Nullable: {col['is_nullable']})")
            
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    apply_migration()
