import axios from 'axios';

// Configure base URL for API requests
const API_URL = `http://${window.location.hostname}:3001/api`;

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
  updateTaskAssignment: (taskId, assigneeId) => axios.patch(`${API_URL}/tasks/${taskId}/assign`, { assignee_id: assigneeId }),
  
  // Users
  getUsers: () => axios.get(`${API_URL}/users`),
  getCurrentUser: () => axios.get(`${API_URL}/users/me`),
  
  // File attachments
  uploadTaskAttachment: (taskId, formData) => axios.post(`${API_URL}/tasks/${taskId}/attachments`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getTaskAttachments: (taskId) => axios.get(`${API_URL}/tasks/${taskId}/attachments`)
};

export default api;
