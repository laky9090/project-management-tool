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
    due_date: new Date().toISOString().split('T')[0],
    assignee_id: ''
  });
  const [fileAttachment, setFileAttachment] = useState(null);
  const [users, setUsers] = useState([]);

  // Fetch available users for assignment
  React.useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await api.getUsers();
        setUsers(response.data);
      } catch (error) {
        console.error('Error fetching users:', error);
      }
    };
    fetchUsers();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      console.log('Attempting to create task:', {
        ...formData,
        project_id: projectId
      });

      const response = await api.createTask({
        ...formData,
        project_id: projectId
      });

      console.log('Task created successfully:', response.data);

      if (fileAttachment && response.data.id) {
        const attachmentFormData = new FormData();
        attachmentFormData.append('file', fileAttachment);
        await api.uploadTaskAttachment(response.data.id, attachmentFormData);
        console.log('File attachment uploaded successfully');
      }

      setFormData({
        title: '',
        description: '',
        status: 'To Do',
        priority: 'Medium',
        assignee: '',
        due_date: new Date().toISOString().split('T')[0],
        assignee_id: ''
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
          <select 
            name="assignee_id"
            value={formData.assignee_id}
            onChange={handleChange}
          >
            <option value="">Select Assignee</option>
            {users.map(user => (
              <option key={user.id} value={user.id}>
                {user.username}
              </option>
            ))}
          </select>
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
