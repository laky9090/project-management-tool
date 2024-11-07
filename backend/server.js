require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const jwt = require('jsonwebtoken');
const tasksRouter = require('./routes/tasks');
const projectsRouter = require('./routes/projects');
const authRouter = require('./routes/auth');
const { authMiddleware } = require('./middleware/auth');

const app = express();
const port = process.env.PORT || 3001;

// Configure CORS
app.use(cors({
  origin: (origin, callback) => {
    // Allow requests from any subdomain of replit.dev
    if (!origin || origin.match(/\.replit\.dev$/) || origin.includes('localhost')) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json());

// API Routes
app.use('/api/auth', authRouter);
app.use('/api/tasks', authMiddleware, tasksRouter);
app.use('/api/projects', projectsRouter); // Removed authMiddleware temporarily

// Serve static files
app.use(express.static(path.join(__dirname, '../frontend/build')));

// Serve React app for any other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/build', 'index.html'));
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
});