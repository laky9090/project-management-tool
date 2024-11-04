require('dotenv').config();
const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const tasksRouter = require('./routes/tasks');
const projectsRouter = require('./routes/projects');
const authRouter = require('./routes/auth');
const { authMiddleware } = require('./middleware/auth');

const app = express();
const port = process.env.PORT || 3001;

app.use(cors({
  origin: ['http://localhost:3000', 'http://0.0.0.0:3000'],
  credentials: true
}));
app.use(express.json());

// Routes
app.use('/api/auth', authRouter);
app.use('/api/tasks', authMiddleware, tasksRouter);
app.use('/api/projects', authMiddleware, projectsRouter);

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
