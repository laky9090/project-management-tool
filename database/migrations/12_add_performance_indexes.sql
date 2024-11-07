-- Add indexes for frequently accessed columns
CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_subtasks_parent ON subtasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_task ON task_dependencies(task_id);

-- Add compound indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_tasks_project_priority_status ON tasks(project_id, priority, status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_project_created ON tasks(project_id, created_at) WHERE deleted_at IS NULL;
