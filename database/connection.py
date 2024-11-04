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
            return None
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        logger.info(f"Executing query: {query}")
        if params:
            logger.info(f"Query parameters: {params}")
        
        cur.execute(query, params)
        conn.commit()
        
        if cur.description:  # If the query returns results
            results = cur.fetchall()
            logger.info(f"Query returned {len(results)} rows")
            return results
        logger.info("Query executed successfully (no results)")
        return []  # Return empty list for non-SELECT queries
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database query error: {str(e)}")
        st.error(f"Database query error: {str(e)}")
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            logger.info("Database connection closed")
