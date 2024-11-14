import axios from 'axios';

// Configure base URL for API requests
const API_URL = '/api';

// Configure axios to include credentials
axios.defaults.withCredentials = true;

const api = {
  // Projects
  getProjects: () => axios.get(`${API_URL}/projects`),
  createProject: (project) => axios.post(`${API_URL}/projects`, project),
  updateProject: (projectId, data) => axios.patch(`${API_URL}/projects/${projectId}`, data),
  deleteProject: (projectId) => axios.delete(`${API_URL}/projects/${projectId}`),
  
  // Tasks
  getProjectTasks: (projectId) => axios.get(`${API_URL}/tasks/project/${projectId}`),
  createTask: async (task) => {
    try {
      const response = await axios.post(`${API_URL}/tasks`, task);
      if (!response.data) {
        throw new Error('No data received from server');
      }
      return response;
    } catch (error) {
      console.error('Error creating task:', error);
      // Add custom error information for better error handling
      throw {
        ...error,
        isTaskCreationError: true,
        taskData: task,
        message: error.response?.data?.error || error.message || 'Failed to create task'
      };
    }
  },
  updateTask: (taskId, data) => axios.patch(`${API_URL}/tasks/${taskId}`, data),
  deleteTask: (taskId) => axios.delete(`${API_URL}/tasks/${taskId}`),
  restoreTask: (taskId) => axios.patch(`${API_URL}/tasks/${taskId}/restore`),
  updateTaskStatus: (taskId, status) => axios.patch(`${API_URL}/tasks/${taskId}/status`, { status }),
  updateTaskAssignment: (taskId, assignee) => axios.patch(`${API_URL}/tasks/${taskId}/assign`, { assignee }),
  
  // File attachments
  uploadTaskAttachment: async (taskId, formData) => {
    try {
      const response = await axios.post(`${API_URL}/tasks/${taskId}/attachments`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response;
    } catch (error) {
      console.error('Error uploading attachment:', error);
      throw error;
    }
  },
  getTaskAttachments: (taskId) => axios.get(`${API_URL}/tasks/${taskId}/attachments`)
};

export default api;
