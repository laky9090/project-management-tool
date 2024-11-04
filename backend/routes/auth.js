const express = require('express');
const router = express.Router();
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const db = require('../db/connection');
const { authMiddleware } = require('../middleware/auth');

// Register new user
router.post('/register', async (req, res) => {
  const { username, password, email } = req.body;
  try {
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);
    
    await db.query('BEGIN');
    
    // Create user
    const userResult = await db.query(
      'INSERT INTO users (username, password_hash, email) VALUES ($1, $2, $3) RETURNING id',
      [username, hashedPassword, email]
    );
    
    // Assign default team_member role
    await db.query(
      `INSERT INTO user_roles (user_id, role_id)
       SELECT $1, id FROM roles WHERE name = 'team_member'`,
      [userResult.rows[0].id]
    );
    
    await db.query('COMMIT');
    res.status(201).json({ message: 'User registered successfully' });
  } catch (err) {
    await db.query('ROLLBACK');
    res.status(500).json({ error: 'Registration failed' });
  }
});

// Login
router.post('/login', async (req, res) => {
  const { username, password } = req.body;
  try {
    const result = await db.query(
      'SELECT id, password_hash FROM users WHERE username = $1',
      [username]
    );
    
    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    const validPassword = await bcrypt.compare(password, result.rows[0].password_hash);
    if (!validPassword) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    const token = jwt.sign(
      { userId: result.rows[0].id },
      process.env.JWT_SECRET,
      { expiresIn: '24h' }
    );
    
    res.json({ token });
  } catch (err) {
    res.status(500).json({ error: 'Login failed' });
  }
});

// Get current user with roles
router.get('/me', authMiddleware, async (req, res) => {
  try {
    const result = await db.query(
      `SELECT u.id, u.username, u.email, array_agg(r.name) as roles
       FROM users u
       LEFT JOIN user_roles ur ON u.id = ur.user_id
       LEFT JOIN roles r ON ur.role_id = r.id
       WHERE u.id = $1
       GROUP BY u.id, u.username, u.email`,
      [req.userId]
    );
    
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch user data' });
  }
});

module.exports = router;
