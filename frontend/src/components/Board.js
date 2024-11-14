import React, { useEffect, useState, useCallback } from 'react';
import TaskForm from './TaskForm';
import api from '../api/api';
import './Board.css';

const Board = ({ projectId }) => {
  const [tasks, setTasks] = useState([]);
  const [deletedTasks, setDeletedTasks] = useState([]);
  const [error, setError] = useState(null);
  const [editingTask, setEditingTask] = useState(null);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [sortConfig, setSortConfig] = useState({ key: 'created_at', direction: 'desc' });

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
      // Format date if it exists
      if (updatedData.due_date) {
        updatedData.due_date = new Date(updatedData.due_date).toISOString().split('T')[0];
      }
      await api.updateTask(taskId, updatedData);
      setTasks(prevTasks => 
        prevTasks.map(task =>
          task.id === taskId ? { ...task, ...updatedData } : task
        )
      );
      setEditingTask(null);
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
      const deletedTask = tasks.find(task => task.id === taskId);
      setTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
      setDeletedTasks(prevDeleted => [...prevDeleted, { ...deletedTask, deleted_at: new Date() }]);
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
      const restoredTask = deletedTasks.find(task => task.id === taskId);
      setDeletedTasks(prevDeleted => prevDeleted.filter(task => task.id !== taskId));
      setTasks(prevTasks => [...prevTasks, { ...restoredTask, deleted_at: null }]);
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
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedTasks.map(task => (
              <tr key={task.id}>
                <td onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setEditingTask(task.id);
                }}>
                  {editingTask === task.id ? (
                    <input
                      type="text"
                      defaultValue={task.title}
                      onClick={(e) => e.stopPropagation()}
                      onBlur={(e) => {
                        const newValue = e.target.value.trim();
                        if (newValue !== task.title) {
                          handleUpdateTask(task.id, { title: newValue });
                        }
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
                <td onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setEditingTask(task.id);
                }}>
                  {editingTask === task.id ? (
                    <input
                      type="text"
                      defaultValue={task.comment || ''}
                      onClick={(e) => e.stopPropagation()}
                      onBlur={(e) => {
                        const newValue = e.target.value.trim();
                        if (newValue !== task.comment) {
                          handleUpdateTask(task.id, { comment: newValue });
                        }
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
                  </select>
                </td>
                <td>
                  <select
                    value={task.priority}
                    onChange={(e) => handleUpdateTask(task.id, { priority: e.target.value })}
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </td>
                <td className="date-column" onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setEditingTask(task.id);
                }}>
                  {editingTask === task.id ? (
                    <input
                      type="date"
                      defaultValue={task.due_date}
                      onClick={(e) => e.stopPropagation()}
                      onBlur={(e) => {
                        const newValue = e.target.value;
                        if (newValue !== task.due_date) {
                          handleUpdateTask(task.id, { due_date: newValue || null });
                        }
                      }}
                      autoFocus
                    />
                  ) : (
                    task.due_date && new Date(task.due_date).toLocaleDateString('fr-FR')
                  )}
                </td>
                <td className="actions-column">
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setEditingTask(editingTask === task.id ? null : task.id);
                    }}
                    className="edit-button"
                    title="Edit"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleDeleteTask(task.id);
                    }}
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
          <h3>Deleted Tasks</h3>
          <div className="table-container">
            <table className="task-table deleted-tasks">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th className="date-column">Deleted Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {deletedTasks.map(task => (
                  <tr key={task.id} className="deleted-task-row">
                    <td>{task.title}</td>
                    <td>
                      <span className={`status-badge ${task.status.toLowerCase().replace(' ', '-')}`}>
                        {task.status}
                      </span>
                    </td>
                    <td>
                      <span className={`priority-indicator ${task.priority.toLowerCase()}`}>
                        {task.priority}
                      </span>
                    </td>
                    <td className="date-column">
                      {new Date(task.deleted_at).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="actions-column">
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleRestoreTask(task.id);
                        }}
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
      )}
    </div>
  );
};

export default Board;
