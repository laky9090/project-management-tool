import streamlit as st
import logging
from database.schema import init_database
from components.project_form import create_project_form, list_projects
from components.task_form import create_task_form
from components.board_view import render_board
from components.timeline_view import render_timeline
from components.task_list import render_task_list
from database.connection import get_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Project Management Tool",
    page_icon="📋",
    layout="wide"
)

# Test database connection first
conn = get_connection()
if not conn:
    st.error("Failed to connect to the database. Please check your database configuration.")
    st.stop()
else:
    conn.close()
    logger.info("Initial database connection test successful")

try:
    # Initialize database
    init_database()
except Exception as e:
    logger.error(f"Database initialization error: {str(e)}")
    st.error("Failed to initialize database. Please check the database configuration and try again.")
    st.stop()

# Load custom CSS
try:
    with open("styles/main.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception as e:
    logger.error(f"Failed to load CSS: {str(e)}")
    st.warning("Some styles might not be loaded correctly.")

# Initialize session states
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'Board'
if 'selected_project' not in st.session_state:
    st.session_state.selected_project = None

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
        st.write("---")
        st.write("## Project Views")
        
        view_options = ["Board", "List", "Timeline"]
        current_view_index = view_options.index(st.session_state.current_view) if st.session_state.current_view in view_options else 0
        
        new_view = st.radio(
            "Select View",
            view_options,
            index=current_view_index
        )
        
        if new_view != st.session_state.current_view:
            logger.info(f"Changing view from {st.session_state.current_view} to {new_view}")
            st.session_state.current_view = new_view
            st.rerun()

# Main content
try:
    if st.session_state.current_view == 'create_project':
        logger.info("Rendering create project form")
        if create_project_form():
            st.session_state.current_view = 'Board'
            st.rerun()

    elif st.session_state.selected_project:
        # Add task button
        if st.button("➕ Add Task"):
            logger.info(f"Opening task form for project {st.session_state.selected_project}")
            create_task_form(st.session_state.selected_project)
        
        # Render selected view with proper error handling
        current_view = st.session_state.current_view
        logger.info(f"Rendering {current_view} view for project {st.session_state.selected_project}")
        
        try:
            if current_view == 'Board':
                render_board(st.session_state.selected_project)
            elif current_view == 'List':
                render_task_list(st.session_state.selected_project)
            elif current_view == 'Timeline':
                render_timeline(st.session_state.selected_project)
        except Exception as e:
            logger.error(f"Error rendering {current_view} view: {str(e)}")
            st.error(f"An error occurred while loading the {current_view} view. Please try again.")
    else:
        st.info("Please select or create a project to get started!")
except Exception as e:
    logger.error(f"Application error: {str(e)}")
    st.error("An error occurred while running the application. Please try again.")
