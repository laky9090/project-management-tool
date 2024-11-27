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
  const { projectId } = req.params;
  let workbook;

  try {
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Pragma', 'no-cache');

    const projectResult = await db.query(
      'SELECT name FROM projects WHERE id = $1',
      [projectId]
    );

    if (projectResult.rows.length === 0) {
      return res.status(404).json({ error: 'Project not found' });
    }

    const projectName = projectResult.rows[0].name;
    const sanitizedProjectName = projectName.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    const filename = `${sanitizedProjectName}_tasks_${new Date().toISOString().split('T')[0]}.xlsx`;

    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);

    const { rows: tasks } = await db.query(
      `SELECT t.*, 
          COALESCE(t.updated_at, t.created_at) as last_update
       FROM tasks t
       WHERE t.project_id = $1 AND t.deleted_at IS NULL
       ORDER BY t.created_at DESC`,
      [projectId]
    );

    workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('Tasks');

    worksheet.columns = [
      { header: 'Title', key: 'title', width: 30 },
      { header: 'Comment', key: 'comment', width: 40 },
      { header: 'Status', key: 'status', width: 15 },
      { header: 'Priority', key: 'priority', width: 15 },
      { header: 'Start Date', key: 'start_date', width: 15 },
      { header: 'End Date', key: 'end_date', width: 15 },
      { header: 'Last Update', key: 'last_update', width: 15 },
      { header: 'Assignee', key: 'assignee', width: 20 }
    ];

    worksheet.getRow(1).font = { bold: true };
    worksheet.getRow(1).fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFE5E7EB' }
    };

    const formatDate = (date) => {
      if (!date) return '';
      const d = new Date(date);
      return d.toLocaleDateString('en-US', {
        month: '2-digit',
        day: '2-digit',
        year: 'numeric'
      });
    };

    tasks.forEach(task => {
      worksheet.addRow({
        title: task.title,
        comment: task.comment || '',
        status: task.status,
        priority: task.priority,
        start_date: task.start_date ? formatDate(task.start_date) : '',
        end_date: task.end_date ? formatDate(task.end_date) : '',
        last_update: formatDate(task.last_update),
        assignee: task.assignee || ''
      });
    });

    worksheet.getColumn('start_date').numFmt = 'mm/dd/yyyy';
    worksheet.getColumn('end_date').numFmt = 'mm/dd/yyyy';
    worksheet.getColumn('last_update').numFmt = 'mm/dd/yyyy';

    worksheet.autoFilter = {
      from: 'A1',
      to: 'H1'
    };

    await workbook.xlsx.write(res);
    res.end();

  } catch (err) {
    console.error('Error exporting tasks:', err);

    if (!res.headersSent) {
      res.status(500).json({ 
        error: 'Failed to export tasks',
        details: process.env.NODE_ENV === 'development' ? err.message : undefined
      });
    } else {
      try {
        res.end();
      } catch (endError) {
        console.error('Error ending response:', endError);
      }
    }

    if (workbook) {
      try {
        workbook = null;
      } catch (cleanupError) {
        console.error('Error cleaning up workbook:', cleanupError);
      }
    }
  }
});

// Duplicate task
router.post('/:taskId/duplicate', async (req, res) => {
  const { taskId } = req.params;

  try {
    await db.query('BEGIN');
    
    // Get the task to duplicate
    const { rows: [task] } = await db.query(
      `SELECT title, comment, status, priority, project_id, assignee, due_date
       FROM tasks
       WHERE id = $1 AND deleted_at IS NULL`,
      [taskId]
    );

    if (!task) {
      await db.query('ROLLBACK');
      return res.status(404).json({ error: 'Task not found' });
    }

    // Create the duplicated task with "(Copy)" suffix
    const { rows: [newTask] } = await db.query(
      `INSERT INTO tasks 
       (project_id, title, comment, status, priority, assignee, due_date, created_at, updated_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
       RETURNING *, COALESCE(updated_at, created_at) as last_update`,
      [
        task.project_id,
        `${task.title} (Copy)`,
        task.comment,
        task.status,
        task.priority,
        task.assignee,
        task.due_date
      ]
    );

    await db.query('COMMIT');
    res.status(201).json(newTask);
  } catch (err) {
    await db.query('ROLLBACK');
    console.error('Error duplicating task:', err);
    res.status(500).json({ error: 'Failed to duplicate task' });
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

// Create new task
router.post('/', async (req, res) => {
  const { project_id, title, comment, status, priority, start_date, end_date, assignee } = req.body;

  if (!project_id || !title) {
    return res.status(400).json({ error: 'Project ID and title are required' });
  }

  // Validate dates if both are provided
  if (start_date && end_date) {
    const startDate = new Date(start_date);
    const endDate = new Date(end_date);
    
    // Ensure both dates are valid
    if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
      return res.status(400).json({ error: 'Invalid date format' });
    }
    
    if (startDate > endDate) {
      return res.status(400).json({ error: 'Start date cannot be later than end date' });
    }
  }

  try {
    const { rows } = await db.query(
      `INSERT INTO tasks (project_id, title, comment, status, priority, start_date, end_date, assignee, created_at, updated_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
       RETURNING *, COALESCE(updated_at, created_at) as last_update`,
      [project_id, title, comment, status || 'To Do', priority || 'Medium', start_date, end_date, assignee]
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
    // Get current task data for date validation
    if (updates.start_date || updates.end_date) {
      const { rows: [currentTask] } = await db.query(
        'SELECT start_date, end_date FROM tasks WHERE id = $1',
        [taskId]
      );

      if (currentTask) {
        const startDate = updates.start_date ? new Date(updates.start_date) : 
                         currentTask.start_date ? new Date(currentTask.start_date) : null;
        const endDate = updates.end_date ? new Date(updates.end_date) : 
                       currentTask.end_date ? new Date(currentTask.end_date) : null;

        // Ensure dates are valid if provided
        if ((startDate && isNaN(startDate.getTime())) || (endDate && isNaN(endDate.getTime()))) {
          return res.status(400).json({ error: 'Invalid date format' });
        }

        if (startDate && endDate && startDate > endDate) {
          return res.status(400).json({ error: 'Start date cannot be later than end date' });
        }
      }
    }

    const allowedUpdates = ['title', 'comment', 'status', 'priority', 'start_date', 'end_date', 'assignee'];
    const filteredUpdates = Object.entries(updates)
      .filter(([key]) => allowedUpdates.includes(key))
      .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});

    if (Object.keys(filteredUpdates).length === 0) {
      return res.status(400).json({ error: 'No valid fields to update' });
    }

    // Handle empty assignee values
    if ('assignee' in filteredUpdates) {
      if (filteredUpdates.assignee === null || 
          filteredUpdates.assignee === undefined || 
          (typeof filteredUpdates.assignee === 'string' && filteredUpdates.assignee.trim() === '')) {
        filteredUpdates.assignee = null;
      } else {
        filteredUpdates.assignee = String(filteredUpdates.assignee).trim();
      }
    }

    const updateFields = Object.keys(filteredUpdates).map((key, index) => `${key} = $${index + 1}`);
    updateFields.push('updated_at = CURRENT_TIMESTAMP');

    const values = Object.entries(filteredUpdates).map(([key, value]) => {
      if (key === 'start_date' || key === 'end_date') {
        if (!value) return null;
        if (typeof value === 'string' && value.includes('/')) {
          const [day, month, year] = value.split('/');
          return `${year}-${month}-${day}`;
        }
        return value;
      }
      if (key === 'assignee') {
        return value === '' ? null : value;
      }
      return value;
    });

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
    const errorMessage = err.message || 'Failed to update task';
    res.status(500).json({ 
      error: 'Failed to update task',
      details: process.env.NODE_ENV === 'development' ? errorMessage : undefined
    });
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

// Undo last task change
router.post('/:taskId/undo', async (req, res) => {
  const { taskId } = req.params;

  try {
    // Start transaction
    await db.query('BEGIN');

    // Get the most recent history entry for this task
    const { rows: historyRows } = await db.query(
      `SELECT * FROM task_history 
       WHERE task_id = $1 
       ORDER BY changed_at DESC 
       LIMIT 1`,
      [taskId]
    );

    if (historyRows.length === 0) {
      await db.query('ROLLBACK');
      return res.status(404).json({ error: 'No history found for this task' });
    }

    const previousState = historyRows[0];

    // Update task with previous state
    const { rows } = await db.query(
      `UPDATE tasks 
       SET title = $1, comment = $2, status = $3, priority = $4, due_date = $5, assignee = $6,
           updated_at = CURRENT_TIMESTAMP
       WHERE id = $7 AND deleted_at IS NULL 
       RETURNING *, COALESCE(updated_at, created_at) as last_update`,
      [
        previousState.title,
        previousState.comment,
        previousState.status,
        previousState.priority,
        previousState.due_date,
        previousState.assignee,
        taskId
      ]
    );

    if (rows.length === 0) {
      await db.query('ROLLBACK');
      return res.status(404).json({ error: 'Task not found' });
    }

    // Delete the used history entry
    await db.query(
      'DELETE FROM task_history WHERE id = $1',
      [previousState.id]
    );

    await db.query('COMMIT');
    res.json(rows[0]);
  } catch (err) {
    await db.query('ROLLBACK');
    console.error('Error undoing task change:', err);
    res.status(500).json({ error: 'Failed to undo task change' });
  }
});

module.exports = router;