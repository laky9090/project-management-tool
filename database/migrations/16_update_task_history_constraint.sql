-- Drop existing foreign key constraint
ALTER TABLE task_history 
    DROP CONSTRAINT IF EXISTS task_history_task_id_fkey;

-- Add new foreign key constraint with CASCADE
ALTER TABLE task_history 
    ADD CONSTRAINT task_history_task_id_fkey 
    FOREIGN KEY (task_id) 
    REFERENCES tasks(id) 
    ON DELETE CASCADE;
