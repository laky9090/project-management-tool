import React, { useState } from 'react';
import api from '../api/api';
import './TaskForm.css';

const TaskForm = ({ projectId, onCancel, onTaskCreated }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'To Do',
    priority: 'Medium',
    assignee: '',
    due_date: new Date().toISOString().split('T')[0]
  });
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    try {
      setIsSubmitting(true);
      setError(null);

      if (!formData.title.trim()) {
        throw new Error('Task title is required');
      }

      const taskData = {
        ...formData,
        project_id: projectId
      };

      const response = await api.createTask(taskData);
      const newTask = response.data;

      if (onTaskCreated) {
        onTaskCreated(newTask);
      }
    } catch (error) {
      console.error('Error creating task:', error);
      setError(error.response?.data?.error || error.message || 'Failed to create task');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
    if (error) setError(null);
  };

  return (
    <div className="task-form-overlay">
      <form onSubmit={handleSubmit} className="task-form">
        <h3>Create New Task</h3>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="form-group">
          <label htmlFor="title">Title *</label>
          <input
            id="title"
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="Task Title"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Description"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="status">Status</label>
            <select 
              id="status"
              name="status" 
              value={formData.status} 
              onChange={handleChange}
            >
              <option value="To Do">To Do</option>
              <option value="In Progress">In Progress</option>
              <option value="Done">Done</option>
            </select>
          </div>
          
          <div className="form-group">
            <label htmlFor="priority">Priority</label>
            <select 
              id="priority"
              name="priority" 
              value={formData.priority} 
              onChange={handleChange}
            >
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="assignee">Assignee</label>
            <input
              id="assignee"
              type="text"
              name="assignee"
              value={formData.assignee}
              onChange={handleChange}
              placeholder="Assignee Name"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="due_date">Due Date</label>
            <input
              id="due_date"
              type="date"
              name="due_date"
              value={formData.due_date}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="form-actions">
          <button 
            type="button" 
            onClick={onCancel} 
            className="cancel-button"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button 
            type="submit" 
            className="submit-button"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Creating...' : 'Create Task'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TaskForm;
