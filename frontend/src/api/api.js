import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

const api = {
  // Projects
  getProjects: () => axios.get(`${API_URL}/projects`),
  createProject: (project) => axios.post(`${API_URL}/projects`, project),
  
  // Tasks
  getProjectTasks: (projectId) => axios.get(`${API_URL}/tasks/project/${projectId}`),
  createTask: (task) => axios.post(`${API_URL}/tasks`, task),
  updateTaskStatus: (taskId, status) => axios.patch(`${API_URL}/tasks/${taskId}/status`, { status })
};

export default api;
