const express = require('express');
const router = express.Router();
const db = require('../db/connection');

// Get tasks by project
router.get('/project/:projectId', async (req, res) => {
  try {
    const { rows } = await db.query(
      'SELECT * FROM tasks WHERE project_id = $1 ORDER BY created_at DESC',
      [req.params.projectId]
    );
    res.json(rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch tasks' });
  }
});

// Create new task
router.post('/', async (req, res) => {
  const { project_id, title, description, status, priority, assignee, due_date } = req.body;
  try {
    const { rows } = await db.query(
      `INSERT INTO tasks 
       (project_id, title, description, status, priority, assignee, due_date)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING *`,
      [project_id, title, description, status, priority, assignee, due_date]
    );
    res.status(201).json(rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to create task' });
  }
});

// Update task status
router.patch('/:taskId/status', async (req, res) => {
  const { status } = req.body;
  try {
    const { rows } = await db.query(
      'UPDATE tasks SET status = $1 WHERE id = $2 RETURNING *',
      [status, req.params.taskId]
    );
    if (rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }
    res.json(rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to update task status' });
  }
});

module.exports = router;
