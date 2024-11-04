import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

def check_project_access(user_id, project_id):
    """Verify user has access to the project"""
    try:
        # Check if user is admin or project member
        result = execute_query("""
            SELECT 1 FROM project_members pm
            WHERE pm.project_id = %s AND pm.user_id = %s
            UNION
            SELECT 1 FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = %s AND r.name = 'admin'
        """, (project_id, user_id, user_id))
        return bool(result)
    except Exception as e:
        logger.error(f"Error checking project access: {str(e)}")
        return False

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project {project_id}")
        
        # Verify user has access to the project
        if not check_project_access(st.session_state.user_id, project_id):
            st.error("You don't have permission to create tasks in this project.")
            return False
        
        # Add debug information
        debug_container = st.container()
        with debug_container:
            st.write("### Debug Information")
            st.write(f"Creating task for project ID: {project_id}")
            st.write(f"Creator ID: {st.session_state.user_id}")
        
        with st.form("task_form"):
            title = st.text_input("Task Title")
            description = st.text_area("Description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            
            # Get list of project members for assignee selection
            members = execute_query("""
                SELECT u.id, u.username 
                FROM users u
                JOIN project_members pm ON u.id = pm.user_id
                WHERE pm.project_id = %s
            """, (project_id,))
            
            member_options = ["Unassigned"] + [m['username'] for m in members] if members else ["Unassigned"]
            assignee = st.selectbox("Assignee", member_options)
            
            due_date = st.date_input("Due Date", min_value=datetime.today())
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("⚠️ Task title is required!")
                    return False
                    
                try:
                    # Get assignee_id if an assignee was selected
                    assignee_id = None
                    if assignee != "Unassigned" and members:
                        assignee_id = next((m['id'] for m in members if m['username'] == assignee), None)
                    
                    # Show the data being inserted
                    with debug_container:
                        st.write("### Task Data")
                        task_data = {
                            "project_id": project_id,
                            "title": title,
                            "description": description,
                            "status": status,
                            "priority": priority,
                            "assignee": assignee,
                            "assignee_id": assignee_id,
                            "creator_id": st.session_state.user_id,
                            "due_date": str(due_date)
                        }
                        st.json(task_data)
                    
                    # Insert task
                    insert_query = '''
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, 
                             assignee_id, creator_id, due_date)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    '''
                    
                    values = (
                        project_id, title, description, status, priority,
                        assignee_id, st.session_state.user_id, due_date
                    )
                    
                    # Show the query being executed
                    with debug_container:
                        st.code(insert_query, language="sql")
                        st.write("Values:", values)
                    
                    result = execute_query(insert_query, values)
                    
                    if result:
                        task_id = result[0]['id']
                        st.success(f"✅ Task created successfully! (ID: {task_id})")
                        
                        # Verify the task exists
                        verify = execute_query(
                            """
                            SELECT t.*, u.username as assignee_name, c.username as creator_name
                            FROM tasks t
                            LEFT JOIN users u ON t.assignee_id = u.id
                            LEFT JOIN users c ON t.creator_id = c.id
                            WHERE t.id = %s
                            """, (task_id,)
                        )
                        if verify:
                            with debug_container:
                                st.write("### Created Task")
                                st.json(verify[0])
                            time.sleep(0.5)
                            st.rerun()
                            return True
                        else:
                            st.error("❌ Task verification failed!")
                            return False
                    else:
                        st.error("❌ Failed to create task - database error")
                        return False
                        
                except Exception as e:
                    st.error(f"❌ Error creating task: {str(e)}")
                    with debug_container:
                        st.error("### Error Details")
                        st.code(f"Type: {type(e).__name__}\nDetails: {str(e)}")
                    return False
                    
    except Exception as e:
        st.error(f"❌ Form error: {str(e)}")
        return False
