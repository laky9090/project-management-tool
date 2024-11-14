import React, { useEffect, useState, useCallback } from 'react';
import TaskForm from './TaskForm';
import api from '../api/api';
import './Board.css';

const Board = ({ projectId }) => {
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState(null);
  const [editingTask, setEditingTask] = useState(null);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [sortConfig, setSortConfig] = useState({ key: 'created_at', direction: 'desc' });

  const loadTasks = useCallback(async () => {
    try {
      setError(null);
      const response = await api.getProjectTasks(projectId);
      setTasks(response.data);
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
      await api.updateTask(taskId, updatedData);
      setTasks(prevTasks => 
        prevTasks.map(task =>
          task.id === taskId ? { ...task, ...updatedData } : task
        )
      );
      // Only clear editingTask after successful update
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
      setTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
      await api.deleteTask(taskId);
    } catch (error) {
      console.error('Error deleting task:', error);
      setError('Failed to delete task. Please try again.');
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
                      onFocus={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                      }}
                      onBlur={(e) => {
                        const newValue = e.target.value.trim();
                        if (newValue !== task.title) {
                          handleUpdateTask(task.id, { title: newValue });
                        }
                      }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          const newValue = e.target.value.trim();
                          if (newValue !== task.title) {
                            handleUpdateTask(task.id, { title: newValue });
                          }
                        }
                      }}
                      onClick={(e) => e.stopPropagation()}
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
                      onFocus={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                      }}
                      onBlur={(e) => {
                        const newValue = e.target.value.trim();
                        if (newValue !== task.comment) {
                          handleUpdateTask(task.id, { comment: newValue });
                        }
                      }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          const newValue = e.target.value.trim();
                          if (newValue !== task.comment) {
                            handleUpdateTask(task.id, { comment: newValue });
                          }
                        }
                      }}
                      onClick={(e) => e.stopPropagation()}
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
                <td onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setEditingTask(task.id);
                }}>
                  {editingTask === task.id ? (
                    <select
                      defaultValue={task.priority}
                      onFocus={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                      }}
                      onBlur={(e) => {
                        const newValue = e.target.value;
                        if (newValue !== task.priority) {
                          handleUpdateTask(task.id, { priority: newValue });
                        }
                      }}
                      onChange={(e) => {
                        const newValue = e.target.value;
                        if (newValue !== task.priority) {
                          handleUpdateTask(task.id, { priority: newValue });
                        }
                      }}
                      onClick={(e) => e.stopPropagation()}
                      autoFocus
                    >
                      <option value="Low">Low</option>
                      <option value="Medium">Medium</option>
                      <option value="High">High</option>
                    </select>
                  ) : (
                    <span className={`priority-indicator ${task.priority.toLowerCase()}`}>
                      {task.priority}
                    </span>
                  )}
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
                      onFocus={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                      }}
                      onBlur={(e) => {
                        const newValue = e.target.value;
                        if (newValue !== task.due_date) {
                          handleUpdateTask(task.id, { due_date: newValue });
                        }
                      }}
                      onChange={(e) => {
                        const newValue = e.target.value;
                        if (newValue !== task.due_date) {
                          handleUpdateTask(task.id, { due_date: newValue });
                        }
                      }}
                      onClick={(e) => e.stopPropagation()}
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
    </div>
  );
};

export default Board;
