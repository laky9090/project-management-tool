-- Create trigger function to save task history before update
CREATE OR REPLACE FUNCTION save_task_history()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO task_history (
        task_id,
        title,
        comment,
        status,
        priority,
        due_date,
        assignee
    )
    VALUES (
        OLD.id,
        OLD.title,
        OLD.comment,
        OLD.status,
        OLD.priority,
        OLD.due_date,
        OLD.assignee
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop existing trigger if exists
DROP TRIGGER IF EXISTS task_history_trigger ON tasks;

-- Create trigger
CREATE TRIGGER task_history_trigger
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION save_task_history();
