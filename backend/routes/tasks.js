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

// Get tasks by project with dependencies and subtasks
router.get('/project/:projectId', async (req, res) => {
  try {
    const { rows: tasks } = await db.query(
      `SELECT t.*, 
          array_agg(DISTINCT jsonb_build_object(
              'id', d.id,
              'title', dt.title,
              'status', dt.status
          )) FILTER (WHERE d.id IS NOT NULL) as dependencies,
          array_agg(DISTINCT jsonb_build_object(
              'id', s.id,
              'title', s.title,
              'description', s.description,
              'completed', s.completed
          )) FILTER (WHERE s.id IS NOT NULL) as subtasks
       FROM tasks t
       LEFT JOIN task_dependencies d ON t.id = d.task_id
       LEFT JOIN tasks dt ON d.depends_on_id = dt.id
       LEFT JOIN subtasks s ON t.id = s.parent_task_id
       WHERE t.project_id = $1 AND t.deleted_at IS NULL
       GROUP BY t.id
       ORDER BY t.created_at DESC`,
      [req.params.projectId]
    );
    
    res.json(tasks);
  } catch (err) {
    console.error('Error fetching tasks:', err);
    res.status(500).json({ error: 'Failed to fetch tasks' });
  }
});

// Update task
router.patch('/:taskId', async (req, res) => {
  const { taskId } = req.params;
  const updates = req.body;

  try {
    const allowedUpdates = ['title', 'description', 'status', 'priority', 'due_date', 'assignee'];
    const updateFields = Object.keys(updates)
      .filter(key => allowedUpdates.includes(key))
      .map((key, index) => `${key} = $${index + 1}`);
    
    const values = Object.keys(updates)
      .filter(key => allowedUpdates.includes(key))
      .map(key => updates[key]);

    if (updateFields.length === 0) {
      return res.status(400).json({ error: 'No valid fields to update' });
    }

    const query = `
      UPDATE tasks 
      SET ${updateFields.join(', ')}, updated_at = CURRENT_TIMESTAMP
      WHERE id = $${values.length + 1}
      RETURNING *
    `;

    const { rows } = await db.query(query, [...values, taskId]);

    if (rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json(rows[0]);
  } catch (err) {
    console.error('Error updating task:', err);
    res.status(500).json({ error: 'Failed to update task' });
  }
});

// Delete task (soft delete)
router.delete('/:taskId', async (req, res) => {
  const { taskId } = req.params;

  try {
    const { rows } = await db.query(
      'UPDATE tasks SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1 RETURNING id',
      [taskId]
    );

    if (rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json({ message: 'Task deleted successfully' });
  } catch (err) {
    console.error('Error deleting task:', err);
    res.status(500).json({ error: 'Failed to delete task' });
  }
});

// Update task status
router.patch('/:taskId/status', async (req, res) => {
  const { taskId } = req.params;
  const { status } = req.body;

  try {
    const { rows } = await db.query(
      'UPDATE tasks SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 RETURNING *',
      [status, taskId]
    );

    if (rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json(rows[0]);
  } catch (err) {
    console.error('Error updating task status:', err);
    res.status(500).json({ error: 'Failed to update task status' });
  }
});

// Update task assignment
router.patch('/:taskId/assign', async (req, res) => {
  const { taskId } = req.params;
  const { assignee } = req.body;

  try {
    const { rows } = await db.query(
      'UPDATE tasks SET assignee = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 RETURNING *',
      [assignee, taskId]
    );

    if (rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json(rows[0]);
  } catch (err) {
    console.error('Error assigning task:', err);
    res.status(500).json({ error: 'Failed to assign task' });
  }
});

module.exports = router;
