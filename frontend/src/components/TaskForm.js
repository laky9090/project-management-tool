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
  const [fileAttachment, setFileAttachment] = useState(null);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      status: 'To Do',
      priority: 'Medium',
      assignee: '',
      due_date: new Date().toISOString().split('T')[0]
    });
    setFileAttachment(null);
    setError(null);
  };

  const handleCancel = () => {
    resetForm();
    if (onCancel) onCancel();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    try {
      setIsSubmitting(true);
      setError(null);
      const taskData = {
        ...formData,
        project_id: projectId
      };

      const response = await api.createTask(taskData);
      const newTask = response.data;

      if (fileAttachment && newTask.id) {
        const attachmentFormData = new FormData();
        attachmentFormData.append('file', fileAttachment);
        await api.uploadTaskAttachment(newTask.id, attachmentFormData);
      }

      // Notify parent component with optimistic update
      if (onTaskCreated) {
        onTaskCreated(newTask);
      }
      await new Promise(resolve => setTimeout(resolve, 100)); // Small delay for state update

      // Reset form and close
      resetForm();
      if (onCancel) onCancel();
    } catch (error) {
      console.error('Error creating task:', error);
      setError(error.response?.data?.error || 'Failed to create task');
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
  };

  const handleFileChange = (e) => {
    setFileAttachment(e.target.files[0]);
  };

  return (
    <form onSubmit={handleSubmit} className="task-form">
      <h3>Create New Task</h3>
      {error && <div className="error-message">{error}</div>}
      <div className="form-group">
        <input
          type="text"
          name="title"
          value={formData.title}
          onChange={handleChange}
          placeholder="Task Title"
          required
        />
      </div>
      <div className="form-group">
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          placeholder="Description"
        />
      </div>
      <div className="form-row">
        <div className="form-group">
          <select name="status" value={formData.status} onChange={handleChange}>
            <option value="To Do">To Do</option>
            <option value="In Progress">In Progress</option>
            <option value="Done">Done</option>
          </select>
        </div>
        <div className="form-group">
          <select name="priority" value={formData.priority} onChange={handleChange}>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
          </select>
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <input
            type="text"
            name="assignee"
            value={formData.assignee}
            onChange={handleChange}
            placeholder="Assignee Name"
          />
        </div>
        <div className="form-group">
          <input
            type="date"
            name="due_date"
            value={formData.due_date}
            onChange={handleChange}
          />
        </div>
      </div>
      <div className="form-group">
        <input
          type="file"
          onChange={handleFileChange}
          accept=".pdf,.txt,.doc,.docx,.png,.jpg,.jpeg"
        />
      </div>
      <div className="form-actions">
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating...' : 'Create Task'}
        </button>
        <button type="button" onClick={handleCancel} className="cancel-button">
          Cancel
        </button>
      </div>
    </form>
  );
};

export default TaskForm;
