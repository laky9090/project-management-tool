-- Add assignee column to tasks table
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assignee VARCHAR(100);
