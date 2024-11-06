import streamlit as st
from database.connection import execute_query
import logging
import json

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATES = {
    "Basic Kanban": ["To Do", "In Progress", "Done"],
    "Extended Kanban": ["Backlog", "To Do", "In Progress", "Review", "Done"],
    "Sprint Board": ["Sprint Backlog", "In Development", "Testing", "Ready for Release", "Released"]
}

def save_board_template(name, columns):
    """Save a board template to the database"""
    try:
        result = execute_query("""
            INSERT INTO board_templates (name, columns)
            VALUES (%s, %s)
            RETURNING id
        """, (name, json.dumps(columns)))
        return result[0]['id'] if result else None
    except Exception as e:
        logger.error(f"Error saving template: {str(e)}")
        return None

def get_board_templates():
    """Get all saved board templates"""
    try:
        templates = execute_query("SELECT id, name, columns FROM board_templates")
        return {template['name']: json.loads(template['columns']) for template in templates} if templates else {}
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}")
        return {}

def render_template_manager():
    """Render the template management interface"""
    st.write("### Board Templates")
    
    # Combine default and custom templates
    all_templates = {**DEFAULT_TEMPLATES, **get_board_templates()}
    
    # Template selection
    selected_template = st.selectbox(
        "Select Template",
        options=list(all_templates.keys()),
        index=0
    )
    
    if selected_template:
        columns = all_templates[selected_template]
        st.write("#### Columns")
        for col in columns:
            st.write(f"- {col}")
    
    # Create new template
    st.write("### Create New Template")
    with st.form("new_template_form"):
        template_name = st.text_input("Template Name")
        columns_input = st.text_area(
            "Columns (one per line)",
            help="Enter column names, one per line"
        )
        
        if st.form_submit_button("Save Template"):
            if template_name and columns_input:
                columns = [col.strip() for col in columns_input.split('\n') if col.strip()]
                if columns:
                    template_id = save_board_template(template_name, columns)
                    if template_id:
                        st.success(f"Template '{template_name}' saved successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to save template")
                else:
                    st.error("Please enter at least one column")
            else:
                st.error("Please fill in all fields")

def apply_template_to_project(project_id, template_columns):
    """Apply a template's columns to tasks in a project"""
    try:
        # Update existing tasks to use new status values
        for idx, status in enumerate(template_columns):
            execute_query("""
                UPDATE tasks 
                SET status = %s 
                WHERE project_id = %s AND status NOT IN %s
            """, (status, project_id, tuple(template_columns)))
        return True
    except Exception as e:
        logger.error(f"Error applying template: {str(e)}")
        return False
