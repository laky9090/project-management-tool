const express = require('express');
const router = express.Router();
const db = require('../db/connection');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;
const ExcelJS = require('exceljs');

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

// Export tasks to Excel
router.get('/project/:projectId/export', async (req, res) => {
  try {
    const { projectId } = req.params;
    
    // Get project name
    const projectResult = await db.query(
      'SELECT name FROM projects WHERE id = $1',
      [projectId]
    );
    
    if (projectResult.rows.length === 0) {
      return res.status(404).json({ error: 'Project not found' });
    }
    
    const projectName = projectResult.rows[0].name;
    
    // Get tasks
    const { rows: tasks } = await db.query(
      `SELECT t.*, 
          COALESCE(t.updated_at, t.created_at) as last_update
       FROM tasks t
       WHERE t.project_id = $1 AND t.deleted_at IS NULL
       ORDER BY t.created_at DESC`,
      [projectId]
    );

    // Create workbook and worksheet
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('Tasks');

    // Add headers
    worksheet.columns = [
      { header: 'Title', key: 'title', width: 30 },
      { header: 'Comment', key: 'comment', width: 40 },
      { header: 'Status', key: 'status', width: 15 },
      { header: 'Priority', key: 'priority', width: 15 },
      { header: 'Due Date', key: 'due_date', width: 15 },
      { header: 'Last Update', key: 'last_update', width: 15 },
      { header: 'Assignee', key: 'assignee', width: 20 }
    ];

    // Style headers
    worksheet.getRow(1).font = { bold: true };
    worksheet.getRow(1).fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFE5E7EB' }
    };

    // Add data
    tasks.forEach(task => {
      worksheet.addRow({
        title: task.title,
        comment: task.comment || '',
        status: task.status,
        priority: task.priority,
        due_date: task.due_date ? new Date(task.due_date).toLocaleDateString() : '',
        last_update: new Date(task.last_update).toLocaleDateString(),
        assignee: task.assignee || ''
      });
    });

    // Auto filter
    worksheet.autoFilter = {
      from: 'A1',
      to: 'G1'
    };

    // Set filename
    const filename = `${projectName.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_tasks.xlsx`;
    
    // Set response headers
    res.setHeader(
      'Content-Type',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    );
    res.setHeader('Content-Disposition', `attachment; filename=${filename}`);

    // Write to response
    await workbook.xlsx.write(res);
    res.end();
  } catch (err) {
    console.error('Error exporting tasks:', err);
    res.status(500).json({ error: 'Failed to export tasks' });
  }
});

// Get tasks by project with dependencies and subtasks
router.get('/project/:projectId', async (req, res) => {
  try {
    const { rows: tasks } = await db.query(
      `SELECT t.*, 
          COALESCE(t.updated_at, t.created_at) as last_update,
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
       WHERE t.project_id = $1
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

// Create new task
router.post('/', async (req, res) => {
  const { project_id, title, comment, status, priority, due_date, assignee } = req.body;

  if (!project_id || !title) {
    return res.status(400).json({ error: 'Project ID and title are required' });
  }

  try {
    const { rows } = await db.query(
      `INSERT INTO tasks (project_id, title, comment, status, priority, due_date, assignee, created_at, updated_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
       RETURNING *, COALESCE(updated_at, created_at) as last_update`,
      [project_id, title, comment, status || 'To Do', priority || 'Medium', due_date, assignee]
    );
    res.status(201).json(rows[0]);
  } catch (err) {
    console.error('Error creating task:', err);
    res.status(500).json({ 
      error: 'Failed to create task',
      details: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
  }
});

// Update task
router.patch('/:taskId', async (req, res) => {
  const { taskId } = req.params;
  const updates = req.body;

  try {
    const allowedUpdates = ['title', 'comment', 'status', 'priority', 'due_date', 'assignee'];
    const updateFields = Object.keys(updates)
      .filter(key => allowedUpdates.includes(key))
      .map((key, index) => `${key} = $${index + 1}`);
    
    const values = Object.keys(updates)
      .filter(key => allowedUpdates.includes(key))
      .map(key => {
        if (key === 'due_date') {
          return updates[key] === '' || updates[key] === null ? null : updates[key];
        }
        return updates[key];
      });

    if (updateFields.length === 0) {
      return res.status(400).json({ error: 'No valid fields to update' });
    }

    updateFields.push('updated_at = CURRENT_TIMESTAMP');

    const query = `
      UPDATE tasks 
      SET ${updateFields.join(', ')}
      WHERE id = $${values.length + 1} AND deleted_at IS NULL
      RETURNING *, COALESCE(updated_at, created_at) as last_update
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
      'UPDATE tasks SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND deleted_at IS NULL RETURNING *',
      [taskId]
    );

    if (rows.length === 0) {
      return res.status(404).json({ error: 'Task not found' });
    }

    res.json(rows[0]);
  } catch (err) {
    console.error('Error deleting task:', err);
    res.status(500).json({ error: 'Failed to delete task' });
  }
});

// Permanently delete task
router.delete('/:taskId/permanent', async (req, res) => {
  const { taskId } = req.params;

  try {
    await db.query('BEGIN');
    
    // First delete related records
    await db.query('DELETE FROM task_dependencies WHERE task_id = $1 OR depends_on_id = $1', [taskId]);
    await db.query('DELETE FROM subtasks WHERE parent_task_id = $1', [taskId]);
    
    // Then delete the task
    const { rows } = await db.query(
      'DELETE FROM tasks WHERE id = $1 AND deleted_at IS NOT NULL RETURNING id',
      [taskId]
    );

    if (rows.length === 0) {
      await db.query('ROLLBACK');
      return res.status(404).json({ error: 'Deleted task not found' });
    }

    await db.query('COMMIT');
    res.json({ message: 'Task permanently deleted' });
  } catch (err) {
    await db.query('ROLLBACK');
    console.error('Error permanently deleting task:', err);
    res.status(500).json({ error: 'Failed to permanently delete task' });
  }
});

// Restore task
router.patch('/:taskId/restore', async (req, res) => {
  const { taskId } = req.params;

  try {
    const { rows } = await db.query(
      'UPDATE tasks SET deleted_at = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND deleted_at IS NOT NULL RETURNING *',
      [taskId]
    );

    if (rows.length === 0) {
      return res.status(404).json({ error: 'Task not found or already restored' });
    }

    res.json(rows[0]);
  } catch (err) {
    console.error('Error restoring task:', err);
    res.status(500).json({ error: 'Failed to restore task' });
  }
});

// Update task status
router.patch('/:taskId/status', async (req, res) => {
  const { taskId } = req.params;
  const { status } = req.body;

  try {
    const { rows } = await db.query(
      'UPDATE tasks SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 AND deleted_at IS NULL RETURNING *',
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
      'UPDATE tasks SET assignee = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 AND deleted_at IS NULL RETURNING *',
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