import axios from 'axios';

const API_URL = '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 600000, // 10 minutes timeout
  withCredentials: true,
  maxContentLength: Infinity,
  maxBodyLength: Infinity
});

// Add response interceptor for error handling and retry logic
api.interceptors.response.use(
  response => response,
  async error => {
    const maxRetries = 3;
    let retries = 0;

    while (retries < maxRetries) {
      try {
        if (error.response?.status === 504) {
          console.log(`Retry attempt ${retries + 1} after timeout...`);
          await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds before retry
          const response = await api.request(error.config);
          return response;
        }
        break;
      } catch (retryError) {
        retries++;
        if (retries === maxRetries) {
          console.error('Max retries reached. Last error:', retryError);
          break;
        }
      }
    }

    if (error.response?.status === 504) {
      console.error('Gateway timeout error. The request took too long to complete.');
    } else if (error.response?.status === 404) {
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
  exportProjectTasks: async (projectId) => {
    try {
      const response = await api.get(`/tasks/project/${projectId}/export`, {
        responseType: 'blob',
        timeout: 600000, // 10 minutes timeout for export
        headers: {
          'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        },
        onDownloadProgress: (progressEvent) => {
          if (progressEvent.lengthComputable) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            console.log(`Download Progress: ${percentCompleted}%`);
          }
        },
      });

      // Create blob URL
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });

      // Get filename from content-disposition header or generate one
      let filename = 'tasks.xlsx';
      const contentDisposition = response.headers['content-disposition'];
      if (contentDisposition) {
        const filenameMatch = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }

      // Create download link and trigger download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();

      // Cleanup
      window.URL.revokeObjectURL(url);

      return response;
    } catch (error) {
      console.error('Error downloading Excel file:', error);
      
      // Handle specific error cases
      if (error.response?.status === 404) {
        throw new Error('Project not found');
      } else if (error.response?.status === 504) {
        throw new Error('The export request timed out. Please try again.');
      } else if (error.code === 'ECONNABORTED') {
        throw new Error('The request took too long to complete. Please try again.');
      }
      
      throw new Error('Failed to download Excel file. Please try again.');
    }
  },
};

export default apiClient;