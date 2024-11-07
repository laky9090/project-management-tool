import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
import logging
import time
from functools import wraps
import hashlib
import json
from datetime import datetime, date

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

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

def generate_etag(data):
    """Generate ETag for data"""
    if isinstance(data, (list, dict)):
        data = json.dumps(data, sort_keys=True, cls=DateTimeEncoder)
    return hashlib.md5(str(data).encode()).hexdigest()

def cache_query(ttl_seconds=300):
    """
    Cache decorator for database queries with TTL and ETag support
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Initialize cache in session state if needed
            if 'query_cache' not in st.session_state:
                st.session_state.query_cache = {}
                
            cache_entry = st.session_state.query_cache.get(cache_key)
            current_time = time.time()
            
            # Return cached result if valid
            if cache_entry and (current_time - cache_entry['timestamp']) < ttl_seconds:
                logger.info(f"Cache hit for query: {cache_key}")
                return cache_entry['data']
            
            # Execute query and cache result
            result = func(*args, **kwargs)
            
            # Generate ETag for the result
            etag = generate_etag(result)
            
            # Cache the result with metadata
            st.session_state.query_cache[cache_key] = {
                'data': result,
                'timestamp': current_time,
                'etag': etag
            }
            
            logger.info(f"Cache miss for query: {cache_key}")
            return result
        return wrapper
    return decorator

@cache_query(ttl_seconds=300)
def execute_query(query, params=None, batch_size=1000):
    """
    Execute database query with caching and batch processing support
    """
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
        
        # For SELECT queries with batch processing
        if query.strip().upper().startswith('SELECT'):
            results = []
            while True:
                batch = cur.fetchmany(batch_size)
                if not batch:
                    break
                results.extend(batch)
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

def batch_execute(queries):
    """
    Execute multiple queries in a single transaction
    """
    conn = None
    cur = None
    try:
        conn = get_connection()
        if not conn:
            logger.error("Failed to establish database connection")
            return False
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        for query, params in queries:
            cur.execute(query, params)
            
        conn.commit()
        logger.info(f"Batch execution completed successfully: {len(queries)} queries")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Batch execution error: {str(e)}")
        return False
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
