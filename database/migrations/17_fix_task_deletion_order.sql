-- Fix task deletion order by ensuring proper cascading
DO $$
BEGIN
    -- First ensure task_history has cascade delete
    IF EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'task_history_task_id_fkey'
        AND table_name = 'task_history'
    ) THEN
        ALTER TABLE task_history DROP CONSTRAINT task_history_task_id_fkey;
    END IF;

    ALTER TABLE task_history 
        ADD CONSTRAINT task_history_task_id_fkey 
        FOREIGN KEY (task_id) 
        REFERENCES tasks(id) 
        ON DELETE CASCADE;

    -- Ensure task_dependencies has cascade delete
    IF EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'task_dependencies_task_id_fkey'
        AND table_name = 'task_dependencies'
    ) THEN
        ALTER TABLE task_dependencies DROP CONSTRAINT task_dependencies_task_id_fkey;
    END IF;

    ALTER TABLE task_dependencies 
        ADD CONSTRAINT task_dependencies_task_id_fkey 
        FOREIGN KEY (task_id) 
        REFERENCES tasks(id) 
        ON DELETE CASCADE;

    -- Ensure subtasks has cascade delete
    IF EXISTS (
        SELECT 1 
        FROM information_schema.table_constraints 
        WHERE constraint_name = 'subtasks_parent_task_id_fkey'
        AND table_name = 'subtasks'
    ) THEN
        ALTER TABLE subtasks DROP CONSTRAINT subtasks_parent_task_id_fkey;
    END IF;

    ALTER TABLE subtasks 
        ADD CONSTRAINT subtasks_parent_task_id_fkey 
        FOREIGN KEY (parent_task_id) 
        REFERENCES tasks(id) 
        ON DELETE CASCADE;

    -- Add an index on deleted_at for better performance
    CREATE INDEX IF NOT EXISTS idx_tasks_deleted_at ON tasks(deleted_at);
END $$;
