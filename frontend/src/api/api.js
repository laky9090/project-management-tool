import axios from 'axios';

// Configure base URL for API requests based on environment
const API_URL = window.location.hostname.includes('replit') 
  ? `${window.location.protocol}//${window.location.hostname.replace('-3000', '-3001')}`
  : 'http://localhost:3001';

// Configure axios instance with proper CORS settings
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 30000  // Increased timeout for slower connections
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Export the configured API object
const apiService = {
  // Projects
  getProjects: () => api.get('/api/projects'),
  getDeletedProjects: () => api.get('/api/projects/deleted'),
  createProject: (project) => api.post('/api/projects', project),
  updateProject: (projectId, data) => api.patch(`/api/projects/${projectId}`, data),
  deleteProject: (projectId) => api.delete(`/api/projects/${projectId}`),
  restoreProject: (projectId) => api.patch(`/api/projects/${projectId}/restore`),
  permanentlyDeleteProject: (projectId) => api.delete(`/api/projects/${projectId}/permanent`),
  
  // Tasks
  getProjectTasks: (projectId) => api.get(`/api/tasks/project/${projectId}`),
  exportProjectTasks: async (projectId) => {
    try {
      const response = await api.get(`/api/tasks/project/${projectId}/export`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'tasks.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/);
        if (filenameMatch && filenameMatch.length === 2) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      return true;
    } catch (error) {
      console.error('Error exporting tasks:', error);
      throw error;
    }
  },
  createTask: (task) => api.post('/api/tasks', task),
  updateTask: async (taskId, data) => {
    try {
      const processedData = { ...data };
      
      // Handle empty values
      if (processedData.comment === '') {
        processedData.comment = null;
      }
      if (processedData.due_date === '') {
        processedData.due_date = null;
      }
      
      // Handle date format conversion for due_date
      if (processedData.due_date && typeof processedData.due_date === 'string') {
        // Check if date is in DD/MM/YYYY format
        const dateRegex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
        const match = processedData.due_date.match(dateRegex);
        if (match) {
          const [, day, month, year] = match;
          processedData.due_date = `${year}-${month}-${day}`;
        }
      }
      
      const response = await api.patch(`/api/tasks/${taskId}`, processedData);
      if (!response.data) {
        throw new Error('No data received from server');
      }
      return response;
    } catch (error) {
      console.error('Error updating task:', error);
      throw error;
    }
  },
  deleteTask: (taskId) => api.delete(`/api/tasks/${taskId}`),
  permanentlyDeleteTask: (taskId) => api.delete(`/api/tasks/${taskId}/permanent`),
  restoreTask: (taskId) => api.patch(`/api/tasks/${taskId}/restore`),
  updateTaskStatus: (taskId, status) => api.patch(`/api/tasks/${taskId}/status`, { status }),
  updateTaskAssignment: (taskId, assignee) => api.patch(`/api/tasks/${taskId}/assign`, { assignee }),
};

export default apiService;
