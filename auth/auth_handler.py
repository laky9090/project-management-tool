import streamlit as st
from database.connection import execute_query
import bcrypt
import jwt
import datetime
import os

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    return jwt.encode(
        {'user_id': user_id, 'exp': expiration},
        os.environ.get('JWT_SECRET', 'your-secret-key'),
        algorithm='HS256'
    )

def verify_jwt_token(token):
    try:
        payload = jwt.decode(
            token,
            os.environ.get('JWT_SECRET', 'your-secret-key'),
            algorithms=['HS256']
        )
        return payload['user_id']
    except:
        return None

def register_user(username, password, email):
    try:
        hashed_password = hash_password(password)
        result = execute_query("""
            INSERT INTO users (username, password_hash, email)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (username, hashed_password.decode('utf-8'), email))
        
        if result:
            # Assign default team_member role
            user_id = result[0]['id']
            execute_query("""
                INSERT INTO user_roles (user_id, role_id)
                SELECT %s, id FROM roles WHERE name = 'team_member'
            """, (user_id,))
            return user_id
        return None
    except Exception as e:
        st.error(f"Registration failed: {str(e)}")
        return None

def login_user(username, password):
    try:
        result = execute_query("""
            SELECT id, password_hash 
            FROM users 
            WHERE username = %s
        """, (username,))
        
        if result and verify_password(password, result[0]['password_hash']):
            user_id = result[0]['id']
            token = create_jwt_token(user_id)
            return token
        return None
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return None

def get_user_roles(user_id):
    try:
        roles = execute_query("""
            SELECT r.name
            FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = %s
        """, (user_id,))
        return [role['name'] for role in roles] if roles else []
    except Exception as e:
        st.error(f"Failed to get user roles: {str(e)}")
        return []

def check_permission(user_id, project_id, required_role=None):
    try:
        # Check if user is admin
        admin_check = execute_query("""
            SELECT 1 FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = %s AND r.name = 'admin'
        """, (user_id,))
        
        if admin_check:
            return True
            
        if required_role:
            # Check specific role for project
            return bool(execute_query("""
                SELECT 1 FROM project_members
                WHERE project_id = %s AND user_id = %s AND role = %s
            """, (project_id, user_id, required_role)))
        else:
            # Check if user is a member of the project
            return bool(execute_query("""
                SELECT 1 FROM project_members
                WHERE project_id = %s AND user_id = %s
            """, (project_id, user_id)))
    except Exception as e:
        st.error(f"Permission check failed: {str(e)}")
        return False
