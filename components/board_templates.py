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
        # Validate inputs
        if not name or not columns:
            return None, "Template name and columns are required"
        if len(columns) < 2:
            return None, "Template must have at least 2 columns"
            
        # Check for duplicate template name
        existing = execute_query(
            "SELECT id FROM board_templates WHERE name = %s",
            (name,)
        )
        if existing:
            return None, "A template with this name already exists"
            
        # Convert columns to JSON string before saving
        columns_json = json.dumps(columns)
        result = execute_query("""
            INSERT INTO board_templates (name, columns)
            VALUES (%s, %s)
            RETURNING id
        """, (name, columns_json))
        return (result[0]['id'], "Template saved successfully") if result else (None, "Failed to save template")
    except Exception as e:
        logger.error(f"Error saving template: {str(e)}")
        return None, f"Error saving template: {str(e)}"

def get_board_templates():
    """Get all saved board templates"""
    try:
        templates = execute_query("SELECT id, name, columns FROM board_templates")
        template_dict = {}
        if templates:
            for template in templates:
                try:
                    columns = json.loads(template['columns']) if isinstance(template['columns'], str) else template['columns']
                    template_dict[template['name']] = columns
                except Exception as e:
                    logger.error(f"Error parsing template columns: {str(e)}")
        return template_dict
    except Exception as e:
        logger.error(f"Error fetching templates: {str(e)}")
        return {}

def render_template_manager():
    """Render the template management interface"""
    st.write("### Custom Board Templates")
    
    # Template creation form
    with st.form("new_template_form"):
        template_name = st.text_input(
            "Template Name",
            help="Enter a unique name for your template"
        )
        
        # Dynamic column input
        st.write("#### Define Columns")
        st.info("Enter one column name per line. Order matters - columns will appear left to right.")
        columns_input = st.text_area(
            "Columns",
            placeholder="To Do\nIn Progress\nDone",
            help="Enter at least 2 columns, one per line"
        )
        
        # Preview current layout
        if columns_input:
            columns = [col.strip() for col in columns_input.split('\n') if col.strip()]
            if columns:
                st.write("#### Preview:")
                cols = st.columns(len(columns))
                for idx, (col, column_name) in enumerate(zip(cols, columns)):
                    with col:
                        st.markdown(f"**{column_name}**")
        
        submitted = st.form_submit_button("Save Template")
        if submitted:
            if template_name and columns_input:
                columns = [col.strip() for col in columns_input.split('\n') if col.strip()]
                template_id, message = save_board_template(template_name, columns)
                if template_id:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please fill in all fields")
    
    # Display existing custom templates
    st.write("### Existing Templates")
    
    # Default templates
    st.write("#### Default Templates")
    for name, columns in DEFAULT_TEMPLATES.items():
        with st.expander(name):
            st.write("Columns:")
            cols = st.columns(len(columns))
            for idx, (col, column_name) in enumerate(zip(cols, columns)):
                with col:
                    st.markdown(f"**{column_name}**")
    
    # Custom templates
    custom_templates = get_board_templates()
    if custom_templates:
        st.write("#### Custom Templates")
        for name, columns in custom_templates.items():
            with st.expander(name):
                st.write("Columns:")
                cols = st.columns(len(columns))
                for idx, (col, column_name) in enumerate(zip(cols, columns)):
                    with col:
                        st.markdown(f"**{column_name}**")
                if st.button(f"Delete {name}", key=f"del_{name}"):
                    if delete_template(name):
                        st.success(f"Template '{name}' deleted")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete template '{name}'")

def delete_template(name):
    """Delete a board template"""
    try:
        result = execute_query(
            "DELETE FROM board_templates WHERE name = %s",
            (name,)
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        return False

def apply_template_to_project(project_id, template_columns):
    """Apply a template's columns to tasks in a project"""
    try:
        # Start transaction
        execute_query("BEGIN")
        
        # Get current task statuses
        current_tasks = execute_query(
            "SELECT id, status FROM tasks WHERE project_id = %s",
            (project_id,)
        )
        
        # Map old statuses to new ones
        if current_tasks:
            old_statuses = list(set(task['status'] for task in current_tasks))
            # Map tasks to closest matching new status or first status
            for status in old_statuses:
                if status not in template_columns:
                    execute_query("""
                        UPDATE tasks 
                        SET status = %s 
                        WHERE project_id = %s AND status = %s
                    """, (template_columns[0], project_id, status))
        
        execute_query("COMMIT")
        return True
    except Exception as e:
        execute_query("ROLLBACK")
        logger.error(f"Error applying template: {str(e)}")
        return False
