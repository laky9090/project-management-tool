import streamlit as st
from database.connection import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    try:
        with open('database/migrations/05_simplify_schema.sql', 'r') as f:
            migration_sql = f.read()
            
        # Execute each statement separately
        statements = migration_sql.split(';')
        for statement in statements:
            if statement.strip():
                execute_query(statement)
                
        return True
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    apply_migration()
