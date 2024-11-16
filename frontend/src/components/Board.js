import React, { useEffect, useState, useCallback } from 'react';
import TaskForm from './TaskForm';
import api from '../api/api';
import './Board.css';
import './task.css';

const Board = ({ projectId }) => {
  const [tasks, setTasks] = useState([]);
  const [deletedTasks, setDeletedTasks] = useState([]);
  const [error, setError] = useState(null);
  const [editingTask, setEditingTask] = useState(null);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [showDeletedTasks, setShowDeletedTasks] = useState(false);
  const [sortConfig, setSortConfig] = useState({ key: 'created_at', direction: 'desc' });

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR'); // This will format as DD/MM/YYYY
  };

  const loadTasks = useCallback(async () => {
    try {
      setError(null);
      const response = await api.getProjectTasks(projectId);
      setTasks(response.data.filter(task => !task.deleted_at));
      setDeletedTasks(response.data.filter(task => task.deleted_at));
    } catch (error) {
      console.error('Error loading tasks:', error);
      setError('Failed to load tasks');
    }
  }, [projectId]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const handleTaskCreated = useCallback((newTask) => {
    setTasks(prevTasks => [newTask, ...prevTasks]);
    setShowTaskForm(false);
    loadTasks();
  }, [loadTasks]);

  const handleUpdateTask = async (taskId, updatedData) => {
    try {
      setError(null);
      if (updatedData.due_date) {
        updatedData.due_date = new Date(updatedData.due_date).toISOString().split('T')[0];
      }
      await api.updateTask(taskId, updatedData);
      loadTasks(); // Reload to get the updated timestamp
    } catch (error) {
      console.error('Error updating task:', error);
      setError('Failed to update task. Please try again.');
      loadTasks();
    }
  };

  const handleDeleteTask = async (taskId) => {
    try {
      setError(null);
      await api.deleteTask(taskId);
      loadTasks();
    } catch (error) {
      console.error('Error deleting task:', error);
      setError('Failed to delete task. Please try again.');
      loadTasks();
    }
  };

  const handleRestoreTask = async (taskId) => {
    try {
      setError(null);
      await api.restoreTask(taskId);
      loadTasks();
    } catch (error) {
      console.error('Error restoring task:', error);
      setError('Failed to restore task. Please try again.');
      loadTasks();
    }
  };

  const handleSort = (key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const sortedTasks = [...tasks].sort((a, b) => {
    if (a[sortConfig.key] < b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (a[sortConfig.key] > b[sortConfig.key]) {
      return sortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  });

  const getSortIcon = (key) => {
    if (sortConfig.key === key) {
      return sortConfig.direction === 'asc' ? ' ↑' : ' ↓';
    }
    return ' ↕';
  };

  return (
    <div className="board">
      {error && <div className="error-message">{error}</div>}

      <button className="add-task-button" onClick={() => setShowTaskForm(true)}>
        ➕ Add New Task
      </button>

      {showTaskForm && (
        <TaskForm
          projectId={projectId}
          onTaskCreated={handleTaskCreated}
          onCancel={() => setShowTaskForm(false)}
        />
      )}

      <div className="table-container">
        <table className="task-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('title')}>
                Title {getSortIcon('title')}
              </th>
              <th onClick={() => handleSort('comment')}>
                Comment {getSortIcon('comment')}
              </th>
              <th onClick={() => handleSort('status')}>
                Status {getSortIcon('status')}
              </th>
              <th onClick={() => handleSort('priority')}>
                Priority {getSortIcon('priority')}
              </th>
              <th onClick={() => handleSort('due_date')} className="date-column">
                Due Date {getSortIcon('due_date')}
              </th>
              <th onClick={() => handleSort('updated_at')} className="date-column">
                Last Update {getSortIcon('updated_at')}
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedTasks.map(task => (
              <tr key={task.id} data-status={task.status}>
                <td onClick={() => setEditingTask(task.id)}>
                  {editingTask === task.id ? (
                    <input
                      type="text"
                      defaultValue={task.title}
                      onBlur={(e) => {
                        const newValue = e.target.value.trim();
                        if (newValue !== task.title) {
                          handleUpdateTask(task.id, { title: newValue });
                        }
                        setEditingTask(null);
                      }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.target.blur();
                        }
                      }}
                      autoFocus
                    />
                  ) : (
                    task.title
                  )}
                </td>
                <td onClick={() => setEditingTask(task.id)}>
                  {editingTask === task.id ? (
                    <input
                      type="text"
                      defaultValue={task.comment || ''}
                      onBlur={(e) => {
                        const newValue = e.target.value.trim();
                        if (newValue !== task.comment) {
                          handleUpdateTask(task.id, { comment: newValue });
                        }
                        setEditingTask(null);
                      }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.target.blur();
                        }
                      }}
                    />
                  ) : (
                    task.comment || ''
                  )}
                </td>
                <td>
                  <select
                    value={task.status}
                    onChange={(e) => handleUpdateTask(task.id, { status: e.target.value })}
                  >
                    <option value="To Do">To Do</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Done">Done</option>
                    <option value="Canceled">Canceled</option>
                  </select>
                </td>
                <td data-priority={task.priority}>
                  <select
                    value={task.priority}
                    onChange={(e) => handleUpdateTask(task.id, { priority: e.target.value })}
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </td>
                <td className="date-column">
                  {editingTask === task.id ? (
                    <input
                      type="date"
                      defaultValue={task.due_date}
                      onBlur={(e) => {
                        const newValue = e.target.value;
                        if (newValue !== task.due_date) {
                          handleUpdateTask(task.id, { due_date: newValue || null });
                        }
                        setEditingTask(null);
                      }}
                    />
                  ) : (
                    formatDate(task.due_date)
                  )}
                </td>
                <td className="date-column">
                  {formatDate(task.updated_at)}
                </td>
                <td className="actions-column">
                  <button
                    onClick={() => setEditingTask(editingTask === task.id ? null : task.id)}
                    className="edit-button"
                    title="Edit"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={() => handleDeleteTask(task.id)}
                    className="delete-button"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {deletedTasks.length > 0 && (
        <div className="deleted-tasks-section">
          <div 
            className="deleted-tasks-header" 
            onClick={() => setShowDeletedTasks(!showDeletedTasks)}
          >
            <h3>
              Deleted Tasks ({deletedTasks.length})
              <span 
                className="toggle-icon"
                style={{ transform: showDeletedTasks ? 'rotate(0deg)' : 'rotate(-90deg)' }}
              >
                ▼
              </span>
            </h3>
          </div>
          <div className={`deleted-tasks-content ${showDeletedTasks ? 'visible' : ''}`}>
            <div className="table-container">
              <table className={`task-table deleted-tasks ${showDeletedTasks ? 'visible' : ''}`}>
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Comment</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th className="date-column">Due Date</th>
                    <th className="date-column">Last Update</th>
                    <th className="date-column">Deleted Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {deletedTasks.map(task => (
                    <tr key={task.id} className="deleted-task-row" data-status={task.status}>
                      <td>{task.title}</td>
                      <td>{task.comment || ''}</td>
                      <td>
                        <span className={`status-badge ${task.status.toLowerCase().replace(' ', '-')}`}>
                          {task.status}
                        </span>
                      </td>
                      <td data-priority={task.priority}>
                        <span className={`priority-indicator ${task.priority.toLowerCase()}`}>
                          {task.priority}
                        </span>
                      </td>
                      <td className="date-column">
                        {formatDate(task.due_date)}
                      </td>
                      <td className="date-column">
                        {formatDate(task.updated_at)}
                      </td>
                      <td className="date-column">
                        {formatDate(task.deleted_at)}
                      </td>
                      <td className="actions-column">
                        <button
                          onClick={() => handleRestoreTask(task.id)}
                          className="restore-button"
                          title="Restore"
                        >
                          🔄
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Board;