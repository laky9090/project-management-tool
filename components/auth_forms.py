import streamlit as st
from database.connection import execute_query
import bcrypt
import jwt
import os

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id):
    try:
        return jwt.encode(
            {'user_id': user_id},
            os.environ['JWT_SECRET'],
            algorithm='HS256'
        )
    except Exception as e:
        st.error(f"Error creating token: {str(e)}")
        return None

def verify_jwt_token(token):
    try:
        payload = jwt.decode(token, os.environ['JWT_SECRET'], algorithms=['HS256'])
        return payload['user_id']
    except:
        return None

def render_auth_forms():
    # Initialize session states
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'remember_me' not in st.session_state:
        st.session_state.remember_me = False
    if 'stored_token' not in st.session_state:
        st.session_state.stored_token = None

    # Check for stored token
    if not st.session_state.user_id and st.session_state.stored_token:
        user_id = verify_jwt_token(st.session_state.stored_token)
        if user_id:
            st.session_state.user_id = user_id
            return
        else:
            # Clear invalid token
            st.session_state.stored_token = None
        
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            st.write("## Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if username and password:
                    result = execute_query("""
                        SELECT u.id, u.password_hash, array_agg(r.name) as roles
                        FROM users u
                        LEFT JOIN user_roles ur ON u.id = ur.user_id
                        LEFT JOIN roles r ON ur.role_id = r.id
                        WHERE u.username = %s
                        GROUP BY u.id, u.password_hash
                    """, (username,))
                    
                    if result and verify_password(password, result[0]['password_hash']):
                        user_id = result[0]['id']
                        st.session_state.user_id = user_id
                        
                        # Store token if remember me is checked
                        if remember_me:
                            token = create_jwt_token(user_id)
                            if token:
                                st.session_state.stored_token = token
                        
                        st.success("Successfully logged in!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please fill in all fields")
    
    with tab2:
        with st.form("register_form"):
            st.write("## Register")
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")
            
            if submitted:
                if new_username and new_email and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        try:
                            # Start transaction
                            conn = execute_query("BEGIN")
                            
                            hashed_password = hash_password(new_password)
                            result = execute_query("""
                                INSERT INTO users (username, password_hash, email)
                                VALUES (%s, %s, %s)
                                RETURNING id
                            """, (new_username, hashed_password.decode('utf-8'), new_email))
                            
                            if result:
                                user_id = result[0]['id']
                                # Assign default team_member role
                                execute_query("""
                                    INSERT INTO user_roles (user_id, role_id)
                                    SELECT %s, id FROM roles WHERE name = 'team_member'
                                """, (user_id,))
                                
                                execute_query("COMMIT")
                                st.success("Registration successful! Please login.")
                                st.rerun()
                            else:
                                execute_query("ROLLBACK")
                                st.error("Registration failed!")
                        except Exception as e:
                            execute_query("ROLLBACK")
                            st.error(f"Registration failed: {str(e)}")
                else:
                    st.error("Please fill in all fields")
