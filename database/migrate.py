import os
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    return psycopg2.connect(
        host=os.environ['PGHOST'],
        database=os.environ['PGDATABASE'],
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD'],
        port=os.environ['PGPORT']
    )

def apply_migrations():
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Read and execute migration file
        with open('database/migrations/01_update_tasks_schema.sql', 'r') as f:
            migration_sql = f.read()
            
        cur.execute(migration_sql)
        conn.commit()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    apply_migrations()
