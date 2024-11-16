const express = require('express');
const router = express.Router();
const db = require('../db/connection');

// Get all projects
router.get('/', async (req, res) => {
  try {
    const { rows } = await db.query(
      'SELECT *, COALESCE(deleted_at, NULL) as deleted_at FROM projects WHERE deleted_at IS NULL ORDER BY created_at DESC'
    );
    res.json(rows || []); // Ensure we always return an array
  } catch (err) {
    console.error('Error fetching projects:', err);
    res.status(500).json({ 
      error: 'Failed to fetch projects',
      details: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
  }
});

// Get deleted projects
router.get('/deleted', async (req, res) => {
  try {
    const { rows } = await db.query(
      `SELECT p.*, 
       COUNT(t.id) as total_tasks,
       COUNT(CASE WHEN t.status = 'Done' THEN 1 END) as completed_tasks
       FROM projects p
       LEFT JOIN tasks t ON p.id = t.project_id
       WHERE p.deleted_at IS NOT NULL
       GROUP BY p.id
       ORDER BY p.deleted_at DESC`
    );
    res.json(rows || []); // Ensure we always return an array
  } catch (err) {
    console.error('Error fetching deleted projects:', err);
    res.status(500).json({ 
      error: 'Failed to fetch deleted projects',
      details: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
  }
});

// Create new project
router.post('/', async (req, res) => {
  const { name, description, deadline } = req.body;
  
  if (!name) {
    return res.status(400).json({ error: 'Project name is required' });
  }

  try {
    const { rows } = await db.query(
      'INSERT INTO projects (name, description, deadline) VALUES ($1, $2, $3) RETURNING *',
      [name, description, deadline]
    );
    res.status(201).json(rows[0]);
  } catch (err) {
    console.error('Error creating project:', err);
    res.status(500).json({ 
      error: 'Failed to create project',
      details: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
  }
});

// Update project
router.patch('/:id', async (req, res) => {
  const { id } = req.params;
  const { name, description, deadline } = req.body;

  if (!name) {
    return res.status(400).json({ error: 'Project name is required' });
  }

  try {
    const { rows } = await db.query(
      'UPDATE projects SET name = $1, description = $2, deadline = $3, updated_at = CURRENT_TIMESTAMP WHERE id = $4 AND deleted_at IS NULL RETURNING *',
      [name, description, deadline, id]
    );

    if (rows.length === 0) {
      return res.status(404).json({ error: 'Project not found' });
    }

    res.json(rows[0]);
  } catch (err) {
    console.error('Error updating project:', err);
    res.status(500).json({ 
      error: 'Failed to update project',
      details: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
  }
});

// Delete project (soft delete)
router.delete('/:id', async (req, res) => {
  const { id } = req.params;

  try {
    await db.query('BEGIN');
    
    // Soft delete the project
    const { rows } = await db.query(
      'UPDATE projects SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1 AND deleted_at IS NULL RETURNING id',
      [id]
    );

    if (rows.length === 0) {
      await db.query('ROLLBACK');
      return res.status(404).json({ error: 'Project not found' });
    }

    // Also soft delete associated tasks
    await db.query(
      'UPDATE tasks SET deleted_at = CURRENT_TIMESTAMP WHERE project_id = $1 AND deleted_at IS NULL',
      [id]
    );

    await db.query('COMMIT');
    res.json({ message: 'Project and associated tasks deleted successfully' });
  } catch (err) {
    await db.query('ROLLBACK');
    console.error('Error deleting project:', err);
    res.status(500).json({ 
      error: 'Failed to delete project',
      details: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
  }
});

// Permanently delete project
router.delete('/:id/permanent', async (req, res) => {
  const { id } = req.params;

  try {
    await db.query('BEGIN');
    
    // First delete all associated tasks
    await db.query('DELETE FROM tasks WHERE project_id = $1', [id]);
    
    // Then delete the project
    const { rows } = await db.query(
      'DELETE FROM projects WHERE id = $1 AND deleted_at IS NOT NULL RETURNING id',
      [id]
    );

    if (rows.length === 0) {
      await db.query('ROLLBACK');
      return res.status(404).json({ error: 'Project not found or not in deleted state' });
    }

    await db.query('COMMIT');
    res.json({ message: 'Project permanently deleted' });
  } catch (err) {
    await db.query('ROLLBACK');
    console.error('Error permanently deleting project:', err);
    res.status(500).json({ 
      error: 'Failed to permanently delete project',
      details: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
  }
});

// Restore project
router.patch('/:id/restore', async (req, res) => {
  const { id } = req.params;

  try {
    await db.query('BEGIN');
    
    const { rows } = await db.query(
      'UPDATE projects SET deleted_at = NULL WHERE id = $1 AND deleted_at IS NOT NULL RETURNING *',
      [id]
    );

    if (rows.length === 0) {
      await db.query('ROLLBACK');
      return res.status(404).json({ error: 'Project not found or already restored' });
    }

    // Also restore associated tasks
    await db.query(
      'UPDATE tasks SET deleted_at = NULL WHERE project_id = $1 AND deleted_at IS NOT NULL',
      [id]
    );

    await db.query('COMMIT');
    res.json(rows[0]);
  } catch (err) {
    await db.query('ROLLBACK');
    console.error('Error restoring project:', err);
    res.status(500).json({ 
      error: 'Failed to restore project',
      details: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
  }
});

module.exports = router;
