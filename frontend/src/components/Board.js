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
  const [loading, setLoading] = useState(true);
  const [updatingTask, setUpdatingTask] = useState(null);

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR');
  };

  const validateDate = (dateStr) => {
    if (!dateStr) return true;
    const regex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
    if (!regex.test(dateStr)) return false;
    
    const [day, month, year] = dateStr.split('/').map(Number);
    const date = new Date(year, month - 1, day);
    return date.getDate() === day &&
           date.getMonth() === month - 1 &&
           date.getFullYear() === year &&
           year >= 1900 && year <= 2100;
  };

  const parseDateInput = (dateStr) => {
    if (!dateStr) return null;
    const [day, month, year] = dateStr.split('/');
    return `${year}-${month}-${day}`;
  };

  const loadTasks = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const response = await api.getProjectTasks(projectId);
      setTasks(response.data.filter(task => !task.deleted_at));
      setDeletedTasks(response.data.filter(task => task.deleted_at));
    } catch (error) {
      console.error('Error loading tasks:', error);
      setError('Failed to load tasks');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const handleExportTasks = async () => {
    try {
      setError(null);
      await api.exportProjectTasks(projectId);
    } catch (error) {
      console.error('Error exporting tasks:', error);
      setError('Failed to export tasks. Please try again.');
    }
  };

  const handleTaskCreated = useCallback((newTask) => {
    setTasks(prevTasks => [newTask, ...prevTasks]);
    setShowTaskForm(false);
    loadTasks();
  }, [loadTasks]);

  const handleUpdateTask = async (taskId, updatedData) => {
    try {
      setError(null);
      setUpdatingTask(taskId);
      let processedData = { ...updatedData };

      // Handle date validation
      if ('due_date' in processedData) {
        if (processedData.due_date && !validateDate(processedData.due_date)) {
          setError('Please enter a valid date in DD/MM/YYYY format');
          return false;
        }
        processedData.due_date = processedData.due_date ? parseDateInput(processedData.due_date) : null;
      }

      await api.updateTask(taskId, processedData);
      await loadTasks();
      setError(null);
      return true;
    } catch (error) {
      console.error('Error updating task:', error);
      setError('Failed to update task. Please try again.');
      return false;
    } finally {
      setUpdatingTask(null);
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

  const handlePermanentDelete = async (taskId) => {
    if (window.confirm('This action cannot be undone. Are you sure you want to permanently delete this task?')) {
      try {
        setError(null);
        await api.permanentlyDeleteTask(taskId);
        setDeletedTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
      } catch (error) {
        console.error('Error permanently deleting task:', error);
        setError('Failed to permanently delete task. Please try again.');
      }
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

  if (loading) {
    return <div className="loading">Loading tasks...</div>;
  }

  return (
    <div className="board">
      {error && (
        <div className="error-message" onClick={() => setError(null)}>
          {error}
          <span className="close-error">×</span>
        </div>
      )}

      <div className="board-actions">
        <button className="add-task-button" onClick={() => setShowTaskForm(true)}>
          ➕ Add New Task
        </button>
        <button className="export-button" onClick={handleExportTasks}>
          📥 Export to Excel
        </button>
      </div>

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
                <td className={editingTask === task.id ? 'editing' : ''}>
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
                    <div onClick={() => setEditingTask(task.id)} className="editable">
                      {task.title}
                    </div>
                  )}
                </td>
                <td className={`comment-cell ${editingTask === task.id ? 'editing' : ''}`}>
                  {editingTask === task.id ? (
                    <textarea
                      defaultValue={task.comment || ''}
                      onBlur={async (e) => {
                        const newValue = e.target.value.trim();
                        if (newValue !== task.comment) {
                          await handleUpdateTask(task.id, { comment: newValue });
                        }
                        setEditingTask(null);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          e.target.blur();
                        }
                      }}
                      autoFocus
                      className="comment-textarea"
                      placeholder="Enter comment..."
                    />
                  ) : (
                    <div 
                      onClick={() => setEditingTask(task.id)} 
                      className="editable comment-content"
                    >
                      {task.comment || ''}
                    </div>
                  )}
                </td>
                <td>
                  <select
                    value={task.status}
                    onChange={(e) => handleUpdateTask(task.id, { status: e.target.value })}
                    className={updatingTask === task.id ? 'updating' : ''}
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
                    className={updatingTask === task.id ? 'updating' : ''}
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </td>
                <td className={`date-column ${editingTask === task.id ? 'editing' : ''}`}>
                  {editingTask === task.id ? (
                    <input
                      type="text"
                      placeholder="DD/MM/YYYY"
                      defaultValue={formatDate(task.due_date)}
                      onBlur={async (e) => {
                        const newValue = e.target.value.trim();
                        if (newValue && !validateDate(newValue)) {
                          setError('Please enter a valid date in DD/MM/YYYY format');
                          e.target.value = formatDate(task.due_date);
                          return;
                        }
                        if (newValue !== formatDate(task.due_date)) {
                          const success = await handleUpdateTask(task.id, { due_date: newValue || null });
                          if (!success) {
                            e.target.value = formatDate(task.due_date);
                          }
                        }
                        setEditingTask(null);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.target.blur();
                        }
                        if (e.key === 'Escape') {
                          e.target.value = formatDate(task.due_date);
                          setEditingTask(null);
                        }
                      }}
                      className={`date-input ${updatingTask === task.id ? 'updating' : ''}`}
                      autoFocus
                    />
                  ) : (
                    <div 
                      onClick={() => setEditingTask(task.id)} 
                      className="editable date-display"
                    >
                      {formatDate(task.due_date)}
                    </div>
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
                        <button
                          onClick={() => handlePermanentDelete(task.id)}
                          className="permanent-delete-button"
                          title="Permanently Delete"
                        >
                          ⛔
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