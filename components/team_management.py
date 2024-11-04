import streamlit as st
from database.connection import execute_query
import logging

logger = logging.getLogger(__name__)

def get_project_members(project_id):
    """Get all members of a project with their roles"""
    return execute_query("""
        SELECT u.id, u.username, u.email, pm.role,
               array_agg(r.name) as global_roles
        FROM users u
        JOIN project_members pm ON u.id = pm.user_id
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        WHERE pm.project_id = %s
        GROUP BY u.id, u.username, u.email, pm.role
    """, (project_id,))

def get_available_users(project_id):
    """Get users not currently in the project"""
    return execute_query("""
        SELECT u.id, u.username, u.email,
               array_agg(r.name) as roles
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        WHERE u.id NOT IN (
            SELECT user_id FROM project_members WHERE project_id = %s
        )
        GROUP BY u.id, u.username, u.email
    """, (project_id,))

def check_project_admin(user_id, project_id):
    """Check if user is project admin or has global admin role"""
    result = execute_query("""
        SELECT 1 FROM project_members
        WHERE project_id = %s AND user_id = %s AND role = 'project_admin'
        UNION
        SELECT 1 FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = %s AND r.name = 'admin'
    """, (project_id, user_id, user_id))
    return bool(result)

def render_team_management(project_id):
    try:
        st.write("## Team Management")
        
        # Verify user has permission to manage team
        if not check_project_admin(st.session_state.user_id, project_id):
            st.warning("You don't have permission to manage team members.")
            return
        
        # Get current team members
        members = get_project_members(project_id)
        
        # Display current team members
        st.write("### Current Team Members")
        if members:
            for member in members:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"**{member['username']}** ({member['email']})")
                    with col2:
                        new_role = st.selectbox(
                            "Role",
                            ["team_member", "project_admin"],
                            index=0 if member['role'] == 'team_member' else 1,
                            key=f"role_{member['id']}"
                        )
                        if new_role != member['role']:
                            execute_query("""
                                UPDATE project_members
                                SET role = %s
                                WHERE project_id = %s AND user_id = %s
                            """, (new_role, project_id, member['id']))
                            st.rerun()
                    with col3:
                        if member['id'] != st.session_state.user_id:  # Can't remove yourself
                            if st.button("Remove", key=f"remove_{member['id']}"):
                                execute_query("""
                                    DELETE FROM project_members
                                    WHERE project_id = %s AND user_id = %s
                                """, (project_id, member['id']))
                                st.rerun()
        else:
            st.info("No team members found.")
        
        # Add new team members
        st.write("### Add Team Members")
        available_users = get_available_users(project_id)
        
        if available_users:
            with st.form("add_member_form"):
                selected_user = st.selectbox(
                    "Select User",
                    options=[(u['id'], f"{u['username']} ({u['email']})") for u in available_users],
                    format_func=lambda x: x[1]
                )
                role = st.selectbox(
                    "Role",
                    ["team_member", "project_admin"]
                )
                
                if st.form_submit_button("Add Member"):
                    execute_query("""
                        INSERT INTO project_members (project_id, user_id, role)
                        VALUES (%s, %s, %s)
                    """, (project_id, selected_user[0], role))
                    st.success(f"Added {selected_user[1]} as {role}")
                    st.rerun()
        else:
            st.info("No available users to add.")
            
    except Exception as e:
        logger.error(f"Error in team management: {str(e)}")
        st.error("An error occurred while managing team members.")
