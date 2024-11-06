-- Create board_templates table
CREATE TABLE IF NOT EXISTS board_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    columns JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default templates
INSERT INTO board_templates (name, columns) VALUES
    ('Basic Kanban', '["To Do", "In Progress", "Done"]'),
    ('Extended Kanban', '["Backlog", "To Do", "In Progress", "Review", "Done"]'),
    ('Sprint Board', '["Sprint Backlog", "In Development", "Testing", "Ready for Release", "Released"]')
ON CONFLICT (name) DO NOTHING;
