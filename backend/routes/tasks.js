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
  console.log('Fetching tasks for project:', req.params.projectId);
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
    
    console.log('Found tasks:', tasks);
    res.json(tasks);
  } catch (err) {
    console.error('Error fetching tasks:', err);
    res.status(500).json({ error: 'Failed to fetch tasks' });
  }
});

// Update task assignment
router.patch('/:taskId/assign', async (req, res) => {
  const { taskId } = req.params;
  const { assignee_id } = req.body;

  try {
    const { rows } = await db.query(
      'UPDATE tasks SET assignee = $1 WHERE id = $2 RETURNING *',
      [assignee_id, taskId]
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

// Create new task with dependencies and subtasks
router.post('/', async (req, res) => {
  console.log('Creating new task with data:', req.body);
  const { 
    project_id, 
    title, 
    description, 
    status, 
    priority, 
    due_date,
    dependencies,
    subtasks,
    assignee_id 
  } = req.body;
  
  if (!project_id) {
    console.error('Missing project_id');
    return res.status(400).json({ error: 'project_id is required' });
  }

  try {
    await db.query('BEGIN');
    
    // Create main task
    const taskResult = await db.query(
      `INSERT INTO tasks (project_id, title, description, status, priority, due_date, assignee)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING *`,
      [project_id, title, description, status, priority, due_date, assignee_id]
    );
    
    const task = taskResult.rows[0];

    // Add dependencies
    if (dependencies && dependencies.length > 0) {
      for (const depId of dependencies) {
        await db.query(
          `INSERT INTO task_dependencies (task_id, depends_on_id)
           VALUES ($1, $2)`,
          [task.id, depId]
        );
      }
    }

    // Add subtasks
    if (subtasks && subtasks.length > 0) {
      for (const subtask of subtasks) {
        await db.query(
          `INSERT INTO subtasks (parent_task_id, title, description, completed)
           VALUES ($1, $2, $3, $4)`,
          [task.id, subtask.title, subtask.description, subtask.completed || false]
        );
      }
    }

    await db.query('COMMIT');
    res.status(201).json(task);
  } catch (err) {
    await db.query('ROLLBACK');
    console.error('Error creating task:', err);
    res.status(500).json({ 
      error: 'Failed to create task',
      details: err.message
    });
  }
});

// Update subtask status
router.patch('/subtasks/:subtaskId', async (req, res) => {
  const { subtaskId } = req.params;
  const { completed } = req.body;

  try {
    const result = await db.query(
      `UPDATE subtasks 
       SET completed = $1,
           status = CASE WHEN $1 THEN 'Done' ELSE 'To Do' END,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $2
       RETURNING *`,
      [completed, subtaskId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Subtask not found' });
    }

    res.json(result.rows[0]);
  } catch (err) {
    console.error('Error updating subtask:', err);
    res.status(500).json({ error: 'Failed to update subtask' });
  }
});

module.exports = router;