import streamlit as st
import logging
from database.schema import init_database
from database.connection import get_connection
from components.project_form import create_project_form, list_projects
from components.task_form import create_task_form
from components.board_view import render_board
from components.analytics import render_analytics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Project Management Tool",
    page_icon="📋",
    layout="wide"
)

# Initialize session states
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'Board'
if 'selected_project' not in st.session_state:
    st.session_state.selected_project = None


try:
    # Initialize database
    init_database()
except Exception as e:
    logger.error(f"Database initialization error: {str(e)}")
    st.error("Failed to initialize database. Please check the configuration.")
    st.stop()

# Sidebar
with st.sidebar:
    st.title("Project Management")

    if st.button("Create New Project"):
        st.session_state.current_view = 'create_project'
        st.rerun()

    st.write("---")
    st.write("## Select Project")
    selected_project = list_projects()

    if selected_project:
        st.session_state.selected_project = selected_project

        # View selection
        st.write("## Project Views")
        view_options = ["Board", "Analytics"]
        selected_view = st.radio("Select View", view_options)
        if selected_view != st.session_state.current_view:
            st.session_state.current_view = selected_view
            st.rerun()

# Main content
try:
    if st.session_state.current_view == 'create_project':
        if create_project_form():
            st.session_state.current_view = 'Board'
            st.rerun()

    elif st.session_state.selected_project:
        if st.session_state.current_view == 'Analytics':
            render_analytics(st.session_state.selected_project)
        else:  # Board view
            render_board(st.session_state.selected_project)
    else:
        st.info("Please select or create a project to get started!")
except Exception as e:
    logger.error(f"Application error: {str(e)}")
    st.error("An error occurred. Please try again.")