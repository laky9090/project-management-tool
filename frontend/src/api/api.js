import axios from 'axios';

// Configure base URL for API requests
const API_URL = process.env.NODE_ENV === 'development' 
  ? window.location.hostname === 'localhost'
    ? 'http://localhost:3001/api'
    : `${window.location.protocol}//${window.location.hostname}:3001/api`
  : '/api';

// Configure axios with CORS settings
const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  }
});

export default {
  // Projects
  getProjects: () => api.get('/projects'),
  getDeletedProjects: () => api.get('/projects/deleted'),
  createProject: (project) => api.post('/projects', project),
  updateProject: (projectId, data) => api.patch(`/projects/${projectId}`, data),
  deleteProject: (projectId) => api.delete(`/projects/${projectId}`),
  restoreProject: (projectId) => api.patch(`/projects/${projectId}/restore`),
  permanentlyDeleteProject: (projectId) => api.delete(`/projects/${projectId}/permanent`),
  
  // Tasks
  getProjectTasks: (projectId) => api.get(`/tasks/project/${projectId}`),
  createTask: async (task) => {
    try {
      const response = await api.post('/tasks', task);
      if (!response.data) {
        throw new Error('No data received from server');
      }
      return response;
    } catch (error) {
      console.error('Error creating task:', error);
      throw error;
    }
  },
  updateTask: (taskId, data) => api.patch(`/tasks/${taskId}`, data),
  deleteTask: (taskId) => api.delete(`/tasks/${taskId}`),
  permanentlyDeleteTask: (taskId) => api.delete(`/tasks/${taskId}/permanent`),
  restoreTask: (taskId) => api.patch(`/tasks/${taskId}/restore`),
  updateTaskStatus: (taskId, status) => api.patch(`/tasks/${taskId}/status`, { status }),
  updateTaskAssignment: (taskId, assignee) => api.patch(`/tasks/${taskId}/assign`, { assignee }),
  
  // File attachments
  uploadTaskAttachment: async (taskId, formData) => {
    try {
      const response = await api.post(`/tasks/${taskId}/attachments`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response;
    } catch (error) {
      console.error('Error uploading attachment:', error);
      throw error;
    }
  },
  getTaskAttachments: (taskId) => api.get(`/tasks/${taskId}/attachments`)
};
