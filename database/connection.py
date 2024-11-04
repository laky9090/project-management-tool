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
        logger.info("Database connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        st.error(f"Database connection error: {str(e)}")
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
        
        # Log the full query with parameters
        if params:
            cur.mogrify(query, params)
            logger.info(f"Executing query: {cur.mogrify(query, params).decode('utf-8')}")
        else:
            logger.info(f"Executing query: {query}")
        
        cur.execute(query, params)
        
        if cur.description:  # If the query returns results
            results = cur.fetchall()
            logger.info(f"Query returned {len(results)} rows")
            if results:
                logger.info(f"First row sample: {results[0]}")
            return results
        
        # For INSERT/UPDATE queries
        conn.commit()
        logger.info("Transaction committed successfully")
        if query.strip().upper().startswith('INSERT'):
            # For INSERT queries, try to get the inserted ID
            try:
                cur.execute("SELECT lastval()")
                last_id = cur.fetchone()['lastval']
                logger.info(f"Last inserted ID: {last_id}")
            except Exception as e:
                logger.warning(f"Could not get last inserted ID: {e}")
        return []
        
    except Exception as e:
        logger.error(f"Query execution error: {str(e)}")
        if conn:
            conn.rollback()
            logger.info("Transaction rolled back due to error")
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            logger.info("Database connection closed")
