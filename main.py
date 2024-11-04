import streamlit as st
from database.schema import init_database
from components.project_form import create_project_form, list_projects
from components.task_form import create_task_form
from components.board_view import render_board
from components.timeline_view import render_timeline
from components.task_list import render_task_list

# Page config
st.set_page_config(
    page_title="Project Management Tool",
    page_icon="📋",
    layout="wide"
)

# Initialize database
init_database()

# Load custom CSS
with open("styles/main.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("Project Management")
    if st.button("Create New Project"):
        st.session_state['current_view'] = 'create_project'
    
    st.write("---")
    st.write("## Select Project")
    selected_project = list_projects()
    
    if selected_project:
        st.session_state['selected_project'] = selected_project
        st.write("---")
        st.write("## Project Views")
        view = st.radio(
            "Select View",
            ["Board", "List", "Timeline"],
            key="view_selector",
            format_func=lambda x: f"📋 {x}" if x == "Board" else f"📑 {x}" if x == "List" else f"📅 {x}"
        )
        st.session_state['current_view'] = view

# Main content
if 'current_view' not in st.session_state:
    st.session_state['current_view'] = 'create_project'

if st.session_state['current_view'] == 'create_project':
    if create_project_form():
        st.session_state['current_view'] = 'Board'
        st.rerun()

elif 'selected_project' in st.session_state:
    # Add task button
    if st.button("➕ Add Task"):
        create_task_form(st.session_state['selected_project'])
    
    # Render selected view
    if st.session_state['current_view'] == 'Board':
        render_board(st.session_state['selected_project'])
    elif st.session_state['current_view'] == 'Timeline':
        render_timeline(st.session_state['selected_project'])
    elif st.session_state['current_view'] == 'List':
        render_task_list(st.session_state['selected_project'])
else:
    st.info("Please select or create a project to get started!")
