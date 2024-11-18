import axios from 'axios';

const API_URL = process.env.NODE_ENV === 'development' 
  ? window.location.hostname === 'localhost'
    ? 'http://localhost:3001/api'
    : `${window.location.protocol}//${window.location.hostname}:3001/api`
  : '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
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
  exportProjectTasks: async (projectId) => {
    try {
      const response = await api.get(`/tasks/project/${projectId}/export`, {
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
  createTask: (task) => api.post('/tasks', task),
  updateTask: (taskId, data) => api.patch(`/tasks/${taskId}`, data),
  deleteTask: (taskId) => api.delete(`/tasks/${taskId}`),
  permanentlyDeleteTask: (taskId) => api.delete(`/tasks/${taskId}/permanent`),
  restoreTask: (taskId) => api.patch(`/tasks/${taskId}/restore`),
  updateTaskStatus: (taskId, status) => api.patch(`/tasks/${taskId}/status`, { status }),
  updateTaskAssignment: (taskId, assignee) => api.patch(`/tasks/${taskId}/assign`, { assignee }),
  duplicateTask: (taskId) => api.post(`/tasks/${taskId}/duplicate`),
};
