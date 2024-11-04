-- Migration to update tasks table schema
ALTER TABLE tasks DROP COLUMN IF EXISTS assignee;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assignee_id INTEGER REFERENCES users(id);
