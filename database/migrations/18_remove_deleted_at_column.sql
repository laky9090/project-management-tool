-- Remove deleted_at column from tasks table
ALTER TABLE tasks DROP COLUMN IF EXISTS deleted_at;
