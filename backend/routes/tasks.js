const express = require('express');
const router = express.Router();
const db = require('../db/connection');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/')
  },
  filename: (req, file, cb) => {
    cb(null, `${Date.now()}-${file.originalname}`)
  }
});

const upload = multer({ storage: storage });

// Create new task
router.post('/', async (req, res) => {
  console.log('Received task creation request with body:', req.body);
  
  const { project_id, title, description, status, priority, assignee, due_date } = req.body;

  // Validation
  if (!project_id || !title) {
    console.log('Missing required fields');
    return res.status(400).json({ 
      error: 'Missing required fields',
      received: { project_id, title }
    });
  }

  try {
    const query = `
      INSERT INTO tasks 
      (project_id, title, description, status, priority, assignee, due_date)
      VALUES ($1, $2, $3, $4, $5, $6, $7)
      RETURNING *
    `;

    const values = [project_id, title, description, status, priority, assignee, due_date];
    console.log('Executing query:', { query, values });

    const { rows } = await db.query(query, values);
    console.log('Query successful, returned row:', rows[0]);

    res.status(201).json(rows[0]);
  } catch (err) {
    console.error('Database error:', err);
    res.status(500).json({ 
      error: 'Failed to create task',
      details: err.message,
      code: err.code
    });
  }
});

// Add file attachment to task
router.post('/:taskId/attachments', upload.single('file'), async (req, res) => {
  const { taskId } = req.params;
  const file = req.file;

  if (!file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  try {
    // Ensure uploads directory exists
    await fs.mkdir('uploads', { recursive: true });

    const query = `
      INSERT INTO file_attachments 
      (task_id, filename, file_path, file_type, file_size)
      VALUES ($1, $2, $3, $4, $5)
      RETURNING *
    `;

    const values = [
      taskId,
      file.originalname,
      file.path,
      file.mimetype,
      file.size
    ];

    const { rows } = await db.query(query, values);
    res.status(201).json(rows[0]);
  } catch (err) {
    console.error('Error uploading file:', err);
    res.status(500).json({ 
      error: 'Failed to upload file',
      details: err.message 
    });
  }
});

// Get task attachments
router.get('/:taskId/attachments', async (req, res) => {
  try {
    const { rows } = await db.query(
      'SELECT * FROM file_attachments WHERE task_id = $1',
      [req.params.taskId]
    );
    res.json(rows);
  } catch (err) {
    console.error('Error fetching attachments:', err);
    res.status(500).json({ error: 'Failed to fetch attachments' });
  }
});

// Check table structure
router.get('/check-table', async (req, res) => {
  try {
    const tableCheck = await db.query(`
      SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'tasks'
      );
    `);
    
    if (!tableCheck.rows[0].exists) {
      await db.query(`
        CREATE TABLE IF NOT EXISTS tasks (
          id SERIAL PRIMARY KEY,
          project_id INTEGER NOT NULL,
          title VARCHAR(255) NOT NULL,
          description TEXT,
          status VARCHAR(50),
          priority VARCHAR(50),
          assignee VARCHAR(255),
          due_date DATE,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);
      return res.json({ message: 'Tasks table created' });
    }

    const columns = await db.query(`
      SELECT column_name, data_type 
      FROM information_schema.columns 
      WHERE table_name = 'tasks';
    `);

    res.json({ 
      message: 'Tasks table exists',
      structure: columns.rows 
    });
  } catch (err) {
    console.error('Error checking table:', err);
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
