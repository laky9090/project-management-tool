import axios from 'axios';

const API_URL = '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
  withCredentials: true
});

// Add response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error);
    if (error.response?.status === 404) {
      console.error('Endpoint not found:', error.config.url);
    }
    return Promise.reject(error);
  }
);

const apiClient = {
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
  createTask: (task) => api.post('/tasks', task),
  updateTask: (taskId, data) => api.patch(`/tasks/${taskId}`, data),
  deleteTask: (taskId) => api.delete(`/tasks/${taskId}`),
  permanentlyDeleteTask: (taskId) => api.delete(`/tasks/${taskId}/permanent`),
  restoreTask: (taskId) => api.patch(`/tasks/${taskId}/restore`),
  updateTaskStatus: (taskId, status) => api.patch(`/tasks/${taskId}/status`, { status }),
  updateTaskAssignment: (taskId, assignee) => api.patch(`/tasks/${taskId}/assign`, { assignee }),
  duplicateTask: (taskId) => api.post(`/tasks/${taskId}/duplicate`),
  undoTaskChange: (taskId) => api.post(`/tasks/${taskId}/undo`),
  exportProjectTasks: (projectId) => api.get(`/tasks/project/${projectId}/export`, { responseType: 'blob' }),
};

export default apiClient;
