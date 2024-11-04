import streamlit as st
from database.connection import execute_query
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

def create_task_form(project_id):
    try:
        logger.info(f"Creating task form for project {project_id}")
        
        with st.form("task_form"):
            # Add debug container
            debug_container = st.container()
            
            title = st.text_input("Task Title")
            description = st.text_area("Description")
            status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            
            # Get list of project members for assignee selection
            members = execute_query('''
                SELECT u.id, u.username 
                FROM users u
                JOIN project_members pm ON u.id = pm.user_id
                WHERE pm.project_id = %s
            ''', (project_id,))
            
            # Create assignee dropdown with user IDs
            member_options = [(None, "Unassigned")] + [(m['id'], m['username']) for m in members] if members else [(None, "Unassigned")]
            assignee_id = st.selectbox(
                "Assignee",
                options=member_options,
                format_func=lambda x: x[1]
            )[0]  # Get the ID part
            
            due_date = st.date_input("Due Date", min_value=datetime.today())
            
            submitted = st.form_submit_button("Create Task")
            
            if submitted:
                if not title:
                    st.error("Task title is required!")
                    return False
                
                try:
                    # Insert task with proper IDs
                    insert_query = '''
                        INSERT INTO tasks 
                            (project_id, title, description, status, priority, 
                             assignee_id, creator_id, due_date)
                        VALUES 
                            (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                    '''
                    
                    values = (
                        project_id,
                        title,
                        description,
                        status,
                        priority,
                        assignee_id,  # This can be None (null) for unassigned
                        st.session_state.user_id,  # Current user is creator
                        due_date
                    )
                    
                    # Show debug info
                    with debug_container:
                        st.write("### Debug Information")
                        st.json({
                            "Query": insert_query,
                            "Values": {
                                "project_id": project_id,
                                "title": title,
                                "status": status,
                                "priority": priority,
                                "assignee_id": assignee_id,
                                "creator_id": st.session_state.user_id,
                                "due_date": str(due_date)
                            }
                        })
                    
                    result = execute_query(insert_query, values)
                    
                    if result:
                        st.success(f"Task created successfully! ID: {result[0]['id']}")
                        time.sleep(0.5)
                        st.rerun()
                        return True
                    else:
                        st.error("Failed to create task - database error")
                        return False
                        
                except Exception as e:
                    st.error(f"Error creating task: {str(e)}")
                    with debug_container:
                        st.error("### Error Details")
                        st.code(f"Type: {type(e).__name__}\nDetails: {str(e)}")
                    return False
                    
    except Exception as e:
        st.error(f"Form error: {str(e)}")
        return False
