-- Update tasks table structure
ALTER TABLE tasks 
  ALTER COLUMN project_id SET NOT NULL,
  ALTER COLUMN title TYPE VARCHAR(255),
  ALTER COLUMN status TYPE VARCHAR(50),
  ALTER COLUMN priority TYPE VARCHAR(50),
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
