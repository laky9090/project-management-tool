from database.connection import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_performance_migration():
    try:
        # Read and execute migration file
        with open('database/migrations/12_add_performance_indexes.sql', 'r') as f:
            sql = f.read()
            
        # Execute migration
        execute_query(sql)
        logger.info("Performance indexes created successfully")
        
        # Verify indexes were created
        result = execute_query("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'tasks'
            AND indexname LIKE 'idx_%'
        """)
        
        if result:
            logger.info("Created indexes:")
            for idx in result:
                logger.info(f"- {idx['indexname']}")
            return True
        else:
            logger.error("No indexes found after migration")
            return False
            
    except Exception as e:
        logger.error(f"Performance migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    apply_performance_migration()
