const express = require('express');
const router = express.Router();
const db = require('../db/connection');

// Get all projects
router.get('/', async (req, res) => {
  try {
    const { rows } = await db.query(
      'SELECT *, COALESCE(deleted_at, NULL) as deleted_at FROM projects WHERE deleted_at IS NULL ORDER BY created_at DESC'
    );
    res.json(rows);
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
      'UPDATE projects SET name = $1, description = $2, deadline = $3 WHERE id = $4 AND deleted_at IS NULL RETURNING *',
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
    const { rows } = await db.query(
      'UPDATE projects SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1 AND deleted_at IS NULL RETURNING id',
      [id]
    );

    if (rows.length === 0) {
      return res.status(404).json({ error: 'Project not found' });
    }

    res.json({ message: 'Project deleted successfully' });
  } catch (err) {
    console.error('Error deleting project:', err);
    res.status(500).json({ 
      error: 'Failed to delete project',
      details: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
  }
});

module.exports = router;
