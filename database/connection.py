import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st

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
        cur.execute(query, params)
        conn.commit()
        
        if cur.description:  # If the query returns results
            return cur.fetchall()
        return []  # Return empty list for non-SELECT queries
        
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"Database query error: {str(e)}")
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
