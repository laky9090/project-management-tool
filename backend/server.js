require('dotenv').config();
const express = require('express');
const cors = require('cors');
const session = require('express-session');
const tasksRouter = require('./routes/tasks');
const projectsRouter = require('./routes/projects');
const authRouter = require('./routes/auth');

const app = express();
const port = process.env.PORT || 3001;

app.use(cors({
  origin: process.env.NODE_ENV === 'production' ? 'https://your-domain.com' : 'http://localhost:3000',
  credentials: true
}));
app.use(express.json());

// Session middleware
app.use(session({
  secret: process.env.SESSION_SECRET || 'development-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Authentication middleware
const authMiddleware = (req, res, next) => {
  if (!req.session.userId) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
};

// Routes
app.use('/api/auth', authRouter);
app.use('/api/tasks', authMiddleware, tasksRouter);
app.use('/api/projects', authMiddleware, projectsRouter);

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
});
