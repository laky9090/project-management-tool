import axios from 'axios';

// Configure base URL for API requests
const API_URL = '/api';

// Configure axios to include credentials
axios.defaults.withCredentials = true;

const api = {
  // Projects
  getProjects: () => axios.get(`${API_URL}/projects`),
  createProject: (project) => axios.post(`${API_URL}/projects`, project),
  
  // Tasks
  getProjectTasks: (projectId) => axios.get(`${API_URL}/tasks/project/${projectId}`),
  createTask: (task) => axios.post(`${API_URL}/tasks`, task),
  updateTask: (taskId, data) => axios.patch(`${API_URL}/tasks/${taskId}`, data),
  deleteTask: (taskId) => axios.delete(`${API_URL}/tasks/${taskId}`),
  updateTaskStatus: (taskId, status) => axios.patch(`${API_URL}/tasks/${taskId}/status`, { status }),
  updateTaskAssignment: (taskId, assignee) => axios.patch(`${API_URL}/tasks/${taskId}/assign`, { assignee }),
  
  // File attachments
  uploadTaskAttachment: (taskId, formData) => axios.post(`${API_URL}/tasks/${taskId}/attachments`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getTaskAttachments: (taskId) => axios.get(`${API_URL}/tasks/${taskId}/attachments`)
};

export default api;
