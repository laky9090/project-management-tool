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
  const [updating, setUpdating] = useState(false);

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR');
  };

  const parseDate = (dateStr) => {
    if (!dateStr) return null;
    if (!dateStr.includes('/')) return dateStr;
    const [day, month, year] = dateStr.split('/');
    return `${year}-${month}-${day}`;
  };

  const validateDate = (dateStr) => {
    if (!dateStr) return true;
    const date = new Date(dateStr);
    return date instanceof Date && !isNaN(date);
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

  const handleUpdateTask = async (taskId, updatedData) => {
    try {
      if (updating) return;
      setUpdating(true);
      setError(null);

      if (updatedData.due_date) {
        if (!validateDate(updatedData.due_date)) {
          throw new Error('Invalid date format');
        }
        updatedData.due_date = parseDate(updatedData.due_date);
      }

      const response = await api.updateTask(taskId, updatedData);
      if (response.data) {
        await loadTasks();
      }
      return true;
    } catch (error) {
      console.error('Error updating task:', error);
      setError('Failed to update task. Please try again.');
      return false;
    } finally {
      setUpdating(false);
    }
  };

  const handleCommentEdit = async (taskId, currentValue) => {
    const cell = document.querySelector(`td[data-task-id="${taskId}"][data-field="comment"]`);
    if (!cell) return;

    const textarea = document.createElement('textarea');
    textarea.value = currentValue || '';
    textarea.style.width = '100%';
    textarea.style.minHeight = '100px';
    textarea.style.resize = 'vertical';

    const originalContent = cell.innerHTML;
    cell.innerHTML = '';
    cell.appendChild(textarea);
    textarea.focus();

    const handleBlur = async () => {
      try {
        const newValue = textarea.value.trim();
        if (newValue !== currentValue) {
          const success = await handleUpdateTask(taskId, { comment: newValue });
          if (!success) {
            cell.innerHTML = originalContent;
          }
        } else {
          cell.innerHTML = originalContent;
        }
      } catch (error) {
        cell.innerHTML = originalContent;
        setError('Failed to update comment. Please try again.');
      }
      textarea.removeEventListener('blur', handleBlur);
    };

    textarea.addEventListener('blur', handleBlur);
  };

  const handleDueDateEdit = async (taskId, currentValue) => {
    const cell = document.querySelector(`td[data-task-id="${taskId}"][data-field="due_date"]`);
    if (!cell) return;

    const input = document.createElement('input');
    input.type = 'date';
    
    if (currentValue) {
      try {
        const [day, month, year] = currentValue.split('/');
        input.value = `${year}-${month}-${day}`;
      } catch (error) {
        console.error('Error parsing date:', error);
        input.value = '';
      }
    }

    const originalContent = cell.innerHTML;
    cell.innerHTML = '';
    cell.appendChild(input);
    input.focus();

    const handleBlur = async () => {
      try {
        if (input.value) {
          if (!validateDate(input.value)) {
            throw new Error('Invalid date format');
          }
          const newDate = new Date(input.value);
          const formattedDate = newDate.toLocaleDateString('fr-FR');
          if (formattedDate !== currentValue) {
            const success = await handleUpdateTask(taskId, { due_date: input.value });
            if (!success) {
              cell.innerHTML = originalContent;
            }
          }
        } else {
          const success = await handleUpdateTask(taskId, { due_date: null });
          if (!success) {
            cell.innerHTML = originalContent;
          }
        }
      } catch (error) {
        cell.innerHTML = originalContent;
        setError('Failed to update due date. Please try again.');
      }
      input.removeEventListener('blur', handleBlur);
    };

    input.addEventListener('blur', handleBlur);
  };

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

  const handleDuplicateTask = async (taskId) => {
    try {
      setError(null);
      const response = await api.duplicateTask(taskId);
      if (response.data) {
        await loadTasks();
      }
    } catch (error) {
      console.error('Error duplicating task:', error);
      setError('Failed to duplicate task. Please try again.');
    }
  };

  const handleSort = (key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const handleUndoTask = async (taskId) => {
    try {
      setError(null);
      setUpdating(true);
      const response = await api.undoTaskChange(taskId);
      if (response.data) {
        await loadTasks();
      }
    } catch (error) {
      console.error('Error undoing task change:', error);
      setError('Failed to undo task change. Please try again.');
    } finally {
      setUpdating(false);
    }
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
      {error && <div className="error-message">{error}</div>}
      {updating && <div className="loading">Updating task...</div>}

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
                <td 
                  onClick={() => setEditingTask(task.id)}
                  data-task-id={task.id}
                  data-field="title"
                >
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
                <td 
                  onClick={() => handleCommentEdit(task.id, task.comment)}
                  data-task-id={task.id}
                  data-field="comment"
                  style={{ whiteSpace: 'pre-wrap' }}
                >
                  {task.comment || ''}
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
                <td 
                  className="date-column"
                  onClick={() => handleDueDateEdit(task.id, formatDate(task.due_date))}
                  data-task-id={task.id}
                  data-field="due_date"
                >
                  {formatDate(task.due_date)}
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
                    onClick={() => handleDuplicateTask(task.id)}
                    className="duplicate-button"
                    title="Duplicate"
                  >
                    📋
                  </button>
                  <button
                    onClick={() => handleUndoTask(task.id)}
                    className="undo-button"
                    title="Undo last change"
                  >
                    ↩️
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
                      <td style={{ whiteSpace: 'pre-wrap' }}>{task.comment || ''}</td>
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