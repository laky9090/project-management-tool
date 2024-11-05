import React, { useState } from 'react';
import api from '../api/api';
import './TaskForm.css';

const TaskForm = ({ projectId }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'To Do',
    priority: 'Medium',
    assignee: '',
    due_date: new Date().toISOString().split('T')[0]
  });
  const [fileAttachment, setFileAttachment] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Debug log before sending
      console.log('Attempting to create task:', {
        ...formData,
        project_id: projectId
      });

      const response = await api.createTask({
        ...formData,
        project_id: projectId
      });

      console.log('Task created successfully:', response.data);

      // Handle file upload if present
      if (fileAttachment && response.data.id) {
        const attachmentFormData = new FormData();
        attachmentFormData.append('file', fileAttachment);
        await api.uploadTaskAttachment(response.data.id, attachmentFormData);
        console.log('File attachment uploaded successfully');
      }

      // Reset form
      setFormData({
        title: '',
        description: '',
        status: 'To Do',
        priority: 'Medium',
        assignee: '',
        due_date: new Date().toISOString().split('T')[0]
      });
      setFileAttachment(null);

      alert('Task created successfully!');

    } catch (error) {
      console.error('Detailed error:', error);
      console.error('Error response:', error.response?.data);
      alert(`Failed to create task: ${error.response?.data?.error || error.message}`);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    setFileAttachment(e.target.files[0]);
  };

  return (
    <form onSubmit={handleSubmit} className="task-form">
      <h3>Create New Task</h3>
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
            placeholder="Assignee"
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
      <button type="submit">Create Task</button>
    </form>
  );
};

export default TaskForm;
