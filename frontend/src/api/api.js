import axios from 'axios';

// Dynamic URL for Replit
const API_URL = process.env.REACT_APP_API_URL || window.location.origin + '/api';

// Configure axios to include credentials
axios.defaults.withCredentials = true;

const api = {
  // Projects
  getProjects: () => axios.get(`${API_URL}/projects`),
  createProject: (project) => axios.post(`${API_URL}/projects`, project),
  
  // Tasks
  getProjectTasks: (projectId) => axios.get(`${API_URL}/tasks/project/${projectId}`),
  createTask: (task) => axios.post(`${API_URL}/tasks`, task),
  updateTaskStatus: (taskId, status) => axios.patch(`${API_URL}/tasks/${taskId}/status`, { status }),
  
  // File attachments
  uploadTaskAttachment: (taskId, formData) => axios.post(`${API_URL}/tasks/${taskId}/attachments`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getTaskAttachments: (taskId) => axios.get(`${API_URL}/tasks/${taskId}/attachments`)
};

export default api;
