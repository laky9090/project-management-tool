const express = require('express');
const router = express.Router();
const bcrypt = require('bcrypt');
const db = require('../db/connection');

// Register endpoint
router.post('/register', async (req, res) => {
  const { username, password, email } = req.body;
  try {
    // Hash password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);
    
    // Create user
    const { rows: [user] } = await db.query(
      'INSERT INTO users (username, password_hash, email) VALUES ($1, $2, $3) RETURNING id',
      [username, hashedPassword, email]
    );
    
    // Assign default team_member role
    await db.query(
      `INSERT INTO user_roles (user_id, role_id) 
       SELECT $1, id FROM roles WHERE name = 'team_member'`,
      [user.id]
    );
    
    res.status(201).json({ success: true });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to register user' });
  }
});

// Login endpoint
router.post('/login', async (req, res) => {
  const { username, password } = req.body;
  try {
    const { rows: [user] } = await db.query(
      'SELECT id, password_hash FROM users WHERE username = $1',
      [username]
    );
    
    if (!user || !(await bcrypt.compare(password, user.password_hash))) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    // Set user session
    req.session.userId = user.id;
    res.json({ success: true });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to login' });
  }
});

// Logout endpoint
router.post('/logout', (req, res) => {
  req.session.destroy();
  res.json({ success: true });
});

// Get current user
router.get('/me', async (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ error: 'Not authenticated' });
  }
  
  try {
    const { rows: [user] } = await db.query(
      `SELECT u.id, u.username, u.email, array_agg(r.name) as roles
       FROM users u
       LEFT JOIN user_roles ur ON u.id = ur.user_id
       LEFT JOIN roles r ON ur.role_id = r.id
       WHERE u.id = $1
       GROUP BY u.id`,
      [req.session.userId]
    );
    
    res.json(user);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch user data' });
  }
});

module.exports = router;
