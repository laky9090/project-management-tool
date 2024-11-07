const express = require('express');
const router = express.Router();
const db = require('../db/connection');

// Get all projects
router.get('/', async (req, res) => {
  try {
    const { rows } = await db.query(
      'SELECT * FROM projects WHERE deleted_at IS NULL ORDER BY created_at DESC'
    );
    res.json(rows);
  } catch (err) {
    console.error('Error fetching projects:', err);
    res.status(500).json({ error: 'Failed to fetch projects', details: err.message });
  }
});

// Create new project
router.post('/', async (req, res) => {
  const { name, description, deadline } = req.body;
  try {
    const { rows } = await db.query(
      'INSERT INTO projects (name, description, deadline) VALUES ($1, $2, $3) RETURNING *',
      [name, description, deadline]
    );
    res.status(201).json(rows[0]);
  } catch (err) {
    console.error('Error creating project:', err);
    res.status(500).json({ error: 'Failed to create project', details: err.message });
  }
});

module.exports = router;
