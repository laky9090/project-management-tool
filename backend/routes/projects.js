const express = require('express');
const router = express.Router();
const db = require('../db/connection');

// Get all projects
router.get('/', async (req, res) => {
  try {
    const { rows } = await db.query(
      'SELECT * FROM projects ORDER BY created_at DESC'
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

// Soft delete project
router.delete('/:id', async (req, res) => {
  const { id } = req.params;
  const { permanent } = req.query;

  try {
    await db.query('BEGIN');
    
    if (permanent === 'true') {
      // First delete all associated tasks
      await db.query('DELETE FROM tasks WHERE project_id = $1', [id]);
      
      // Then delete the project permanently
      const { rows } = await db.query(
        'DELETE FROM projects WHERE id = $1 RETURNING id',
        [id]
      );

      if (rows.length === 0) {
        await db.query('ROLLBACK');
        return res.status(404).json({ error: 'Project not found' });
      }
    } else {
      // Soft delete the project
      const { rows } = await db.query(
        'UPDATE projects SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1 AND deleted_at IS NULL RETURNING id',
        [id]
      );

      if (rows.length === 0) {
        await db.query('ROLLBACK');
        return res.status(404).json({ error: 'Project not found or already deleted' });
      }
    }

    await db.query('COMMIT');
    res.json({ 
      message: permanent === 'true' 
        ? 'Project and associated tasks permanently deleted' 
        : 'Project moved to trash'
    });
  } catch (err) {
    await db.query('ROLLBACK');
    console.error('Error deleting project:', err);
    res.status(500).json({ 
      error: 'Failed to delete project',
      details: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
  }
});

// Restore project
router.post('/:id/restore', async (req, res) => {
  const { id } = req.params;

  try {
    const { rows } = await db.query(
      'UPDATE projects SET deleted_at = NULL WHERE id = $1 AND deleted_at IS NOT NULL RETURNING *',
      [id]
    );

    if (rows.length === 0) {
      return res.status(404).json({ error: 'Project not found or not deleted' });
    }

    res.json(rows[0]);
  } catch (err) {
    console.error('Error restoring project:', err);
    res.status(500).json({ 
      error: 'Failed to restore project',
      details: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
  }
});

module.exports = router;
