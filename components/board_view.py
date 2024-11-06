import streamlit as st
from database.connection import execute_query
from utils.file_handler import save_uploaded_file, get_task_attachments
import logging
import time

logger = logging.getLogger(__name__)

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

def update_subtask_status(subtask_id, completed):
    """Update subtask completion status"""
    try:
        execute_query("BEGIN")
        result = execute_query("""
            UPDATE subtasks
            SET completed = %s,
                status = CASE WHEN %s THEN 'Done' ELSE 'To Do' END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, title, status;
        """, (completed, completed, subtask_id))
        
        if result:
            execute_query("COMMIT")
            return True
        else:
            execute_query("ROLLBACK")
            return False
    except Exception as e:
        execute_query("ROLLBACK")
        logger.error(f"Error updating subtask status: {str(e)}")
        return False

def render_task_card(task):
    with st.container():
        # Task header with edit button
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{task['title']}**")
        with col2:
            new_status = st.selectbox(
                "Status",
                ["To Do", "In Progress", "Done"],
                index=["To Do", "In Progress", "Done"].index(task['status']),
                key=f"status_{task['id']}"
            )
        with col3:
            if st.button("✏️ Edit", key=f"edit_{task['id']}"):
                st.session_state[f"edit_mode_{task['id']}"] = True

        # Edit mode
        if st.session_state.get(f"edit_mode_{task['id']}", False):
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

                if st.form_submit_button("Save Changes"):
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
            # Display task details
            if task['description']:
                st.write(task['description'])
            st.write(f"Priority: **{task['priority']}**")
            if task['due_date']:
                st.write(f"Due: {task['due_date'].strftime('%Y-%m-%d')}")

            # Dependencies and Subtasks section
            with st.expander("Dependencies & Subtasks"):
                # Dependencies section
                st.write("**Dependencies:**")
                dependencies = get_task_dependencies(task['id'])
                if dependencies:
                    for dep in dependencies:
                        st.write(f"- {dep['title']} ({dep['status']})")
                else:
                    st.write("No dependencies")

                # Subtasks section
                st.write("**Subtasks:**")
                subtasks = get_task_subtasks(task['id'])
                if subtasks:
                    for subtask in subtasks:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"- {subtask['title']}")
                        with col2:
                            completed = st.checkbox(
                                "Done",
                                value=subtask['completed'],
                                key=f"subtask_{subtask['id']}"
                            )
                            if completed != subtask['completed']:
                                if update_subtask_status(subtask['id'], completed):
                                    st.rerun()
                else:
                    st.write("No subtasks")

def render_board(project_id):
    """Render project board"""
    st.write("### Project Board")
    
    # Add new task button
    if st.button("➕ Add New Task"):
        st.session_state.show_task_form = True

    # Task creation form
    if st.session_state.get('show_task_form', False):
        with st.form("new_task_form"):
            title = st.text_input("Task Title")
            description = st.text_area("Description")
            col1, col2, col3 = st.columns(3)
            with col1:
                status = st.selectbox("Status", ["To Do", "In Progress", "Done"])
            with col2:
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            with col3:
                due_date = st.date_input("Due Date")

            # Dependencies selection
            available_tasks = execute_query(
                "SELECT id, title FROM tasks WHERE project_id = %s",
                (project_id,)
            )
            if available_tasks:
                dependencies = st.multiselect(
                    "Dependencies",
                    options=[(t['id'], t['title']) for t in available_tasks],
                    format_func=lambda x: x[1]
                )

            # Subtasks
            st.write("### Subtasks")
            num_subtasks = st.number_input("Number of subtasks", min_value=0, max_value=5)
            subtasks = []
            for i in range(num_subtasks):
                st.write(f"#### Subtask {i+1}")
                subtask_title = st.text_input(f"Title", key=f"subtask_title_{i}")
                subtask_desc = st.text_area(f"Description", key=f"subtask_desc_{i}")
                if subtask_title:
                    subtasks.append({
                        'title': subtask_title,
                        'description': subtask_desc,
                        'completed': False
                    })

            if st.form_submit_button("Create Task"):
                try:
                    # Start transaction
                    execute_query("BEGIN")

                    # Create main task
                    task_result = execute_query("""
                        INSERT INTO tasks (project_id, title, description, status, priority, due_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (project_id, title, description, status, priority, due_date))

                    if task_result:
                        task_id = task_result[0]['id']

                        # Add dependencies
                        if dependencies:
                            for dep_id, _ in dependencies:
                                execute_query("""
                                    INSERT INTO task_dependencies (task_id, depends_on_id)
                                    VALUES (%s, %s)
                                """, (task_id, dep_id))

                        # Add subtasks
                        for subtask in subtasks:
                            execute_query("""
                                INSERT INTO subtasks (parent_task_id, title, description, completed)
                                VALUES (%s, %s, %s, %s)
                            """, (task_id, subtask['title'], subtask['description'], subtask['completed']))

                        execute_query("COMMIT")
                        st.success("Task created successfully!")
                        st.session_state.show_task_form = False
                        st.rerun()
                    else:
                        execute_query("ROLLBACK")
                        st.error("Failed to create task")
                except Exception as e:
                    execute_query("ROLLBACK")
                    logger.error(f"Error creating task: {str(e)}")
                    st.error(f"Error creating task: {str(e)}")

    # Display existing tasks grouped by status
    tasks = execute_query("""
        SELECT t.*, array_agg(td.depends_on_id) as dependencies
        FROM tasks t
        LEFT JOIN task_dependencies td ON t.id = td.task_id
        WHERE t.project_id = %s
        GROUP BY t.id
        ORDER BY t.created_at DESC
    """, (project_id,))

    if tasks:
        # Group tasks by status
        task_groups = {"To Do": [], "In Progress": [], "Done": []}
        for task in tasks:
            task_groups[task['status']].append(task)

        # Create columns for each status
        columns = st.columns(len(task_groups))
        for i, (status, status_tasks) in enumerate(task_groups.items()):
            with columns[i]:
                st.write(f"### {status}")
                for task in status_tasks:
                    render_task_card(task)
    else:
        st.info("No tasks found. Create your first task to get started!")
