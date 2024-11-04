import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

// Configure axios to include credentials
axios.defaults.withCredentials = true;

const api = {
  // Auth
  login: (credentials) => axios.post(`${API_URL}/auth/login`, credentials),
  logout: () => axios.post(`${API_URL}/auth/logout`),
  register: (userData) => axios.post(`${API_URL}/auth/register`, userData),
  getCurrentUser: () => axios.get(`${API_URL}/auth/me`),
  
  // Projects
  getProjects: () => axios.get(`${API_URL}/projects`),
  createProject: (project) => axios.post(`${API_URL}/projects`, project),
  
  // Tasks
  getProjectTasks: (projectId) => axios.get(`${API_URL}/tasks/project/${projectId}`),
  createTask: (task) => axios.post(`${API_URL}/tasks`, task),
  updateTaskStatus: (taskId, status) => axios.patch(`${API_URL}/tasks/${taskId}/status`, { status })
};

export default api;
