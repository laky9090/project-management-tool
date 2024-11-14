from database.connection import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_rename_migration():
    try:
        # Read and execute migration file
        with open('database/migrations/13_rename_description_to_comment.sql', 'r') as f:
            sql = f.read()
            
        # Execute migration
        execute_query(sql)
        logger.info("Column renamed successfully")
        
        # Verify column was renamed
        result = execute_query("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tasks' 
            AND column_name = 'comment';
        """)
        
        if result:
            logger.info("Column rename verified")
            return True
        else:
            logger.error("Column rename verification failed")
            return False
            
    except Exception as e:
        logger.error(f"Column rename migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    apply_rename_migration()
