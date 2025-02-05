import streamlit as st
from database.connection import execute_query
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

def convert_datetime(dt):
    """Convert datetime object to ISO format string"""
    try:
        return dt.isoformat() if dt else None
    except Exception as e:
        logger.error(f"Error converting datetime: {str(e)}")
        return None

def convert_project_dates(project):
    """Convert all datetime fields in a project dict to ISO format strings"""
    try:
        project['created_at'] = convert_datetime(project['created_at'])
        project['updated_at'] = convert_datetime(project.get('updated_at'))
        project['deleted_at'] = convert_datetime(project.get('deleted_at'))
        project['deadline'] = convert_datetime(project.get('deadline'))
        return project
    except Exception as e:
        logger.error(f"Error converting project dates: {str(e)}")
        return project

def create_project_form():
    """Create new project form"""
    if 'show_project_form' not in st.session_state:
        st.session_state.show_project_form = False

    if not st.session_state.show_project_form:
        # Add unique key to the create project button
        if st.button("➕ Create New Project", key="create_project_button_main"):
            st.session_state.show_project_form = True
            st.rerun()
        return False

    with st.form("project_form"):
        st.write("### Create Project")

        name = st.text_input("Project Name", key="project_name_input")
        description = st.text_area("Description", key="project_description_input")
        deadline = st.date_input("Deadline", key="project_deadline_input")

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Create Project")
        with col2:
            cancelled = st.form_submit_button("Cancel")

        if cancelled:
            st.session_state.show_project_form = False
            st.rerun()
            return False

        if submitted:
            if not name:
                st.error("Project name is required!")
                return False

            try:
                execute_query("BEGIN")
                result = execute_query('''
                    INSERT INTO projects (name, description, deadline, created_at, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id, name
                    ''',
                    (name, description, deadline)
                )

                if result:
                    execute_query("COMMIT")
                    st.success(f"Project '{name}' created successfully!")
                    st.session_state.show_project_form = False
                    time.sleep(0.5)
                    return True

                execute_query("ROLLBACK")
                st.error("Failed to create project - database error")
                return False

            except Exception as e:
                execute_query("ROLLBACK")
                logger.error(f"Error creating project: {str(e)}")
                st.error(f"Error creating project: {str(e)}")
                return False
    return False

def list_projects():
    """List all projects"""
    try:
        projects = execute_query('''
            SELECT p.*,
                   COUNT(t.id) as total_tasks,
                   COUNT(CASE WHEN t.status = 'Done' THEN 1 END) as completed_tasks
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id AND t.deleted_at IS NULL
            WHERE p.deleted_at IS NULL
            GROUP BY p.id
            ORDER BY p.created_at DESC
        ''')

        selected_project = None

        # Add unique key to the header button
        if st.button("Create New Project", key="create_project_button_header"):
            st.session_state.show_project_form = True
            st.rerun()

        if projects:
            st.markdown("### Active Projects")
            for project in projects:
                project = convert_project_dates(project)
                with st.container():
                    col1, col2 = st.columns([8, 2])

                    with col1:
                        # Each project button already has a unique key
                        if st.button(
                            f"{project['name']} ({project['completed_tasks']}/{project['total_tasks']} tasks)",
                            key=f"select_project_{project['id']}"
                        ):
                            selected_project = project['id']

                    with col2:
                        st.markdown(f"Due: {datetime.fromisoformat(project['deadline']).strftime('%d/%m/%Y') if project['deadline'] else 'No deadline'}")
        else:
            st.info("Please select or create a project to get started!")

        return selected_project

    except Exception as e:
        logger.error(f"Error in list_projects: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        return None

if __name__ == "__main__":
    selected_project = list_projects()
    if selected_project:
        st.write(f"Selected project: {selected_project}")
    else:
        create_project_form()