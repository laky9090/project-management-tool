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
        
        # Verify connection is working
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
            if cur.fetchone()[0] != 1:
                raise Exception("Connection test failed")
        
        logger.info("Database connection established and verified")
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None

def execute_query(query, params=None, use_cache=True):
    conn = None
    cur = None
    try:
        conn = get_connection()
        if not conn:
            logger.error("Failed to establish database connection")
            return None
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Log the query and parameters
        if params:
            formatted_query = cur.mogrify(query, params).decode('utf-8')
            logger.info(f"Executing query: {formatted_query}")
        else:
            logger.info(f"Executing query: {query}")
        
        cur.execute(query, params)
        
        # For SELECT queries
        if query.strip().upper().startswith('SELECT'):
            results = cur.fetchall()
            logger.info(f"SELECT query returned {len(results)} rows")
            if results:
                logger.info(f"First row: {results[0]}")
            return results
            
        # For INSERT queries
        elif query.strip().upper().startswith('INSERT'):
            try:
                # Get the inserted row if RETURNING clause is used
                if 'RETURNING' in query.upper():
                    result = cur.fetchall()
                    if result:
                        logger.info(f"INSERT query returned: {result}")
                        conn.commit()
                        return result
                    else:
                        logger.error("INSERT query didn't return any results")
                        conn.rollback()
                        return None
                else:
                    # For INSERT without RETURNING clause
                    conn.commit()
                    logger.info("INSERT query executed successfully")
                    return []
            except Exception as e:
                logger.error(f"Error processing INSERT results: {str(e)}")
                conn.rollback()
                return None
                
        # For UPDATE/DELETE queries
        else:
            conn.commit()
            logger.info(f"Query executed successfully (affected rows: {cur.rowcount})")
            return []
            
    except Exception as e:
        logger.error(f"Query execution error: {str(e)}")
        if conn:
            conn.rollback()
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            logger.info("Database connection closed")
