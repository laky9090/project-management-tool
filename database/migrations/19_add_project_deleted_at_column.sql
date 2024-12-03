-- Add deleted_at column to projects table
ALTER TABLE projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
