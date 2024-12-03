import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file, get_task_attachments
from components.task_form import create_task_form
import logging
import time

logger = logging.getLogger(__name__)

def delete_task(task_id):
    """Delete task permanently"""
    try:
        execute_query("BEGIN")
        
        # Delete task dependencies first
        execute_query("""
            DELETE FROM task_dependencies 
            WHERE task_id = %s OR depends_on_id = %s
        """, (task_id, task_id))
        
        # Delete subtasks
        execute_query("""
            DELETE FROM subtasks 
            WHERE parent_task_id = %s
        """, (task_id,))
        
        # Finally delete the task
        result = execute_query("""
            DELETE FROM tasks 
            WHERE id = %s 
            RETURNING id
        """, (task_id,))
        
        if result:
            execute_query("COMMIT")
            # Clear cache after successful deletion
            if 'query_cache' in st.session_state:
                st.session_state.query_cache.clear()
            return True
            
        execute_query("ROLLBACK")
        return False
    except Exception as e:
        execute_query("ROLLBACK")
        logger.error(f"Error deleting task: {str(e)}")
        return False

def delete_subtask(subtask_id):
    try:
        execute_query("BEGIN")
        result = execute_query(
            "DELETE FROM subtasks WHERE id = %s RETURNING id",
            (subtask_id,)
        )
        if result:
            execute_query("COMMIT")
            return True
        execute_query("ROLLBACK")
        return False
    except Exception as e:
        execute_query("ROLLBACK")
        logger.error(f"Error deleting subtask: {str(e)}")
        return False

def get_task_dependencies(task_id):
    """Get dependencies for a task"""
    try:
        logger.info(f"Fetching dependencies for task {task_id}")
        dependencies = execute_query("""
            SELECT t.id, t.title, t.status, t.priority
            FROM tasks t
            JOIN task_dependencies td ON t.id = td.depends_on_id
            WHERE td.task_id = %s
            ORDER BY t.created_at DESC
        """, (task_id,))
        logger.info(f"Found {len(dependencies) if dependencies else 0} dependencies")
        return dependencies if dependencies else []
    except Exception as e:
        logger.error(f"Error fetching dependencies for task {task_id}: {str(e)}")
        return []

def get_task_subtasks(task_id):
    """Get subtasks for a task"""
    try:
        logger.info(f"Fetching subtasks for task {task_id}")
        subtasks = execute_query("""
            SELECT id, title, description, status, completed
            FROM subtasks
            WHERE parent_task_id = %s
            ORDER BY created_at
        """, (task_id,))
        logger.info(f"Found {len(subtasks) if subtasks else 0} subtasks")
        return subtasks if subtasks else []
    except Exception as e:
        logger.error(f"Error fetching subtasks for task {task_id}: {str(e)}")
        return []

def update_task_assignee(task_id, assignee):
    try:
        result = execute_query("""
            UPDATE tasks 
            SET assignee = %s 
            WHERE id = %s 
            RETURNING id
        """, (assignee, task_id))
        return bool(result)
    except Exception as e:
        logger.error(f"Error updating task assignee: {str(e)}")
        return False

def render_task_card(task, is_deleted=False):
    with st.container():
        col1, col2, col3 = st.columns([4, 1, 1])
        
        with col1:
            st.markdown(f"### {task['title']}")
            
        with col2:
            if not is_deleted:
                if st.button("✏️", key=f"edit_{task['id']}", help="Edit task"):
                    st.session_state[f"edit_mode_{task['id']}"] = True
                    
        with col3:
            if not is_deleted:
                if st.button("🗑️", key=f"delete_{task['id']}", help="Delete task"):
                    if st.button("Confirm Delete", key=f"confirm_delete_{task['id']}"):
                        if delete_task(task['id']):
                            st.warning("Task deleted permanently")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Failed to delete task")

        if task['comment']:
            st.write(task['comment'])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Priority:** {task['priority']}")
        with col2:
            st.write(f"**Due Date:** {task['due_date'].strftime('%d/%m/%Y') if task['due_date'] else 'Not set'}")
        with col3:
            if not is_deleted:
                new_status = st.selectbox(
                    "Status",
                    ["To Do", "In Progress", "Done", "Canceled"],
                    index=["To Do", "In Progress", "Done", "Canceled"].index(task['status']),
                    key=f"status_{task['id']}"
                )
                if new_status != task['status']:
                    if execute_query(
                        "UPDATE tasks SET status = %s WHERE id = %s",
                        (new_status, task['id'])
                    ):
                        # Clear cache after status update
                        if 'query_cache' in st.session_state:
                            st.session_state.query_cache.clear()
                        st.rerun()

        # Assignee field
        new_assignee = st.text_input(
            "Assignee",
            value=task['assignee'] if task['assignee'] else '',
            key=f"assignee_{task['id']}",
            placeholder="Click to assign"
        )
        if new_assignee != task['assignee']:
            if update_task_assignee(task['id'], new_assignee):
                st.success(f"Task assigned to {new_assignee}")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Failed to update assignee")

        # Edit form with cancel button
        if not is_deleted and st.session_state.get(f"edit_mode_{task['id']}", False):
            with st.form(key=f"edit_task_{task['id']}"):
                new_title = st.text_input("Title", value=task['title'])
                new_description = st.text_area("Description", value=task['description'])
                
                col1, col2 = st.columns(2)
                with col1:
                    new_priority = st.selectbox(
                        "Priority",
                        ["Low", "Medium", "High"],
                        index=["Low", "Medium", "High"].index(task['priority'])
                    )
                with col2:
                    new_due_date = st.date_input("Due Date", value=task['due_date'])
                
                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("Save Changes")
                with col2:
                    cancel = st.form_submit_button("Cancel")

                if submit and new_title:
                    try:
                        result = execute_query('''
                            UPDATE tasks 
                            SET title = %s, description = %s, priority = %s, due_date = %s
                            WHERE id = %s
                            RETURNING id
                        ''', (new_title, new_description, new_priority, new_due_date, task['id']))
                        
                        if result:
                            st.success("Task updated successfully!")
                            st.session_state[f"edit_mode_{task['id']}"] = False
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Failed to update task")
                    except Exception as e:
                        st.error(f"Error updating task: {str(e)}")
                
                if cancel:
                    st.session_state[f"edit_mode_{task['id']}"] = False
                    st.rerun()

        # Dependencies section
        if not is_deleted:
            st.write("**Dependencies:**")
            dependencies = get_task_dependencies(task['id'])
            if dependencies:
                for dep in dependencies:
                    st.markdown(f"- {dep['title']} ({dep['status']}) - {dep['priority']} priority")
            else:
                st.write("*No dependencies*")

            # Subtasks section
            st.write("**Subtasks:**")
            subtasks = get_task_subtasks(task['id'])
            if subtasks:
                for subtask in subtasks:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"- {subtask['title']}")
                        if subtask['description']:
                            st.write(f"  *{subtask['description']}*")
                    with col2:
                        completed = st.checkbox(
                            "Complete",
                            value=subtask['completed'],
                            key=f"subtask_{subtask['id']}"
                        )
                        if completed != subtask['completed']:
                            if update_subtask_status(subtask['id'], completed):
                                st.rerun()
                    with col3:
                        if st.button("🗑️", key=f"delete_subtask_{subtask['id']}", help="Delete subtask"):
                            if delete_subtask(subtask['id']):
                                st.success("Subtask deleted successfully!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Failed to delete subtask")
            else:
                st.write("*No subtasks*")

def render_board(project_id):
    """Render project board with tasks grouped by status"""
    try:
        st.write("## Project Board")
        
        # Add new task button
        if st.button("➕ Add New Task"):
            st.session_state.show_task_form = True

        # Show task creation form with cancel button
        if st.session_state.get('show_task_form', False):
            col1, col2 = st.columns([1, 6])
            with col1:
                if st.button("❌ Cancel", key="cancel_task_form"):
                    st.session_state.show_task_form = False
                    st.rerun()
            with col2:
                if create_task_form(project_id):
                    # Clear cache after task creation
                    if 'query_cache' in st.session_state:
                        st.session_state.query_cache.clear()
                    st.session_state.show_task_form = False
                    st.rerun()

        # Fetch and display tasks
        tasks = execute_query("""
            SELECT t.*, 
                array_agg(DISTINCT jsonb_build_object(
                    'id', d.id,
                    'title', dt.title,
                    'status', dt.status
                )) FILTER (WHERE d.id IS NOT NULL) as dependencies,
                array_agg(DISTINCT jsonb_build_object(
                    'id', s.id,
                    'title', s.title,
                    'description', s.description,
                    'completed', s.completed
                )) FILTER (WHERE s.id IS NOT NULL) as subtasks
            FROM tasks t
            LEFT JOIN task_dependencies d ON t.id = d.task_id
            LEFT JOIN tasks dt ON d.depends_on_id = dt.id
            LEFT JOIN subtasks s ON t.id = s.parent_task_id
            WHERE t.project_id = %s AND t.deleted_at IS NULL
            GROUP BY t.id
            ORDER BY t.created_at DESC
        """, (project_id,))

        if tasks:
            task_groups = {"To Do": [], "In Progress": [], "Done": [], "Canceled": []}
            for task in tasks:
                task_groups[task['status']].append(task)

            cols = st.columns(len(task_groups))
            for i, (status, status_tasks) in enumerate(task_groups.items()):
                with cols[i]:
                    st.write(f"### {status}")
                    for task in status_tasks:
                        with st.container():
                            render_task_card(task)
        else:
            st.info("No active tasks found. Create your first task to get started!")

        # Removed deleted tasks section as part of removing soft deletion functionality
            
    except Exception as e:
        logger.error(f"Error rendering board: {str(e)}")
        st.error("An error occurred while loading the board. Please try again.")