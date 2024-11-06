import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ['PGHOST'],
            database=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            port=os.environ['PGPORT']
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None

def execute_query(query, params=None):
    conn = None
    cur = None
    try:
        conn = get_connection()
        if not conn:
            logger.error("Failed to establish database connection")
            return None
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Log query details
        if params:
            formatted_query = cur.mogrify(query, params).decode('utf-8')
            logger.info(f"Executing query: {formatted_query}")
        else:
            logger.info(f"Executing query: {query}")
            
        cur.execute(query, params)
        
        # For SELECT queries
        if query.strip().upper().startswith('SELECT'):
            results = cur.fetchall()
            logger.info(f"Query returned {len(results)} rows")
            return results
            
        # For INSERT/UPDATE/DELETE
        else:
            try:
                if 'RETURNING' in query.upper():
                    result = cur.fetchall()
                    if result:
                        conn.commit()
                        logger.info(f"Query executed successfully, returned: {result}")
                        return result
                else:
                    conn.commit()
                    logger.info("Query executed successfully")
                    return []
            except Exception as e:
                conn.rollback()
                logger.error(f"Query failed: {str(e)}")
                return None
                
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Query execution error: {str(e)}")
        return None
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            logger.info("Database connection closed")
