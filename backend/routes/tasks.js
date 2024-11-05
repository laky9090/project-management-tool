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

// Get tasks by project
router.get('/project/:projectId', async (req, res) => {
  console.log('Fetching tasks for project:', req.params.projectId);
  try {
    const { rows } = await db.query(
      'SELECT * FROM tasks WHERE project_id = $1 ORDER BY created_at DESC',
      [req.params.projectId]
    );
    console.log('Found tasks:', rows);
    res.json(rows);
  } catch (err) {
    console.error('Error fetching tasks:', err);
    res.status(500).json({ error: 'Failed to fetch tasks' });
  }
});

// Create new task
router.post('/', async (req, res) => {
  console.log('Creating new task with data:', req.body);
  const { project_id, title, description, status, priority, assignee, due_date } = req.body;
  
  // Validation
  if (!project_id) {
    console.error('Missing project_id');
    return res.status(400).json({ error: 'project_id is required' });
  }

  try {
    // Verify project exists
    const projectCheck = await db.query(
      'SELECT id FROM projects WHERE id = $1',
      [project_id]
    );
    
    if (projectCheck.rows.length === 0) {
      console.error('Project not found:', project_id);
      return res.status(404).json({ error: 'Project not found' });
    }

    const result = await db.query(
      `INSERT INTO tasks 
       (project_id, title, description, status, priority, assignee, due_date)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING *`,
      [project_id, title, description, status, priority, assignee, due_date]
    );
    
    console.log('Task created:', result.rows[0]);
    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error('Error creating task:', err);
    res.status(500).json({ 
      error: 'Failed to create task',
      details: err.message,
      sqlState: err.code
    });
  }
});

// Add file attachment to task
router.post('/:taskId/attachments', upload.single('file'), async (req, res) => {
  const { taskId } = req.params;
  const file = req.file;

  if (!file) {
    console.error('No file uploaded for task:', taskId);
    return res.status(400).json({ error: 'No file uploaded' });
  }

  try {
    // Ensure task exists
    const taskCheck = await db.query(
      'SELECT id FROM tasks WHERE id = $1',
      [taskId]
    );

    if (taskCheck.rows.length === 0) {
      console.error('Task not found:', taskId);
      return res.status(404).json({ error: 'Task not found' });
    }

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

    console.log('Saving file attachment:', {
      taskId,
      filename: file.originalname,
      type: file.mimetype,
      size: file.size
    });

    const { rows } = await db.query(query, values);
    console.log('File attachment saved:', rows[0]);
    res.status(201).json(rows[0]);
  } catch (err) {
    console.error('Error uploading file:', err);
    res.status(500).json({ 
      error: 'Failed to upload file',
      details: err.message,
      code: err.code
    });
  }
});

// Get task attachments
router.get('/:taskId/attachments', async (req, res) => {
  console.log('Fetching attachments for task:', req.params.taskId);
  try {
    const { rows } = await db.query(
      'SELECT * FROM file_attachments WHERE task_id = $1',
      [req.params.taskId]
    );
    console.log('Found attachments:', rows);
    res.json(rows);
  } catch (err) {
    console.error('Error fetching attachments:', err);
    res.status(500).json({ error: 'Failed to fetch attachments' });
  }
});

module.exports = router;
