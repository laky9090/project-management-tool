import React, { useEffect, useState, useCallback } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import api from '../api/api';
import './Board.css';

const Board = ({ projectId }) => {
  const [tasks, setTasks] = useState({ 'To Do': [], 'In Progress': [], 'Done': [] });
  const [error, setError] = useState(null);
  const [editingTask, setEditingTask] = useState(null);

  const loadTasks = useCallback(async () => {
    try {
      setError(null);
      const response = await api.getProjectTasks(projectId);
      
      const groupedTasks = response.data.reduce((acc, task) => {
        if (!acc[task.status]) acc[task.status] = [];
        acc[task.status].push(task);
        return acc;
      }, { 'To Do': [], 'In Progress': [], 'Done': [] });
      
      setTasks(groupedTasks);
    } catch (error) {
      console.error('Error loading tasks:', error);
      setError('Failed to load tasks. Please try again later.');
    }
  }, [projectId]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const onDragEnd = async (result) => {
    if (!result.destination) return;

    const { source, destination, draggableId } = result;
    if (source.droppableId === destination.droppableId) return;

    try {
      setError(null);
      await api.updateTaskStatus(draggableId, destination.droppableId);
      await loadTasks();
    } catch (error) {
      console.error('Error updating task status:', error);
      setError('Failed to update task status. Please try again.');
    }
  };

  const handleAssigneeChange = async (taskId, assignee, oldValue) => {
    try {
      setError(null);
      await api.updateTaskAssignment(taskId, assignee);
      await loadTasks();
    } catch (error) {
      console.error('Error updating task assignment:', error);
      setError('Failed to update task assignment. Please try again.');
      const tasksCopy = { ...tasks };
      Object.keys(tasksCopy).forEach(status => {
        const task = tasksCopy[status].find(t => t.id === taskId);
        if (task) task.assignee = oldValue;
      });
      setTasks(tasksCopy);
    }
  };

  const handleDeleteTask = async (taskId) => {
    try {
      setError(null);
      await api.deleteTask(taskId);
      await loadTasks();
    } catch (error) {
      console.error('Error deleting task:', error);
      setError('Failed to delete task. Please try again.');
    }
  };

  const handleUpdateTask = async (taskId, updatedData) => {
    try {
      setError(null);
      await api.updateTask(taskId, updatedData);
      setEditingTask(null);
      await loadTasks();
    } catch (error) {
      console.error('Error updating task:', error);
      setError('Failed to update task. Please try again.');
    }
  };

  const debounce = (func, wait) => {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  };

  const debouncedAssigneeChange = debounce(handleAssigneeChange, 500);

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="board">
        {error && <div className="error-message">{error}</div>}
        <div className="board-columns">
          {Object.entries(tasks).map(([status, statusTasks]) => (
            <div key={status} className="column">
              <h3>{status}</h3>
              <Droppable droppableId={status}>
                {(provided) => (
                  <div
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                    className="task-list"
                  >
                    {statusTasks.map((task, index) => (
                      <Draggable
                        key={task.id}
                        draggableId={task.id.toString()}
                        index={index}
                      >
                        {(provided) => (
                          <div
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            className="task-card"
                          >
                            {editingTask === task.id ? (
                              <div className="task-edit-form">
                                <input
                                  type="text"
                                  defaultValue={task.title}
                                  onBlur={(e) => handleUpdateTask(task.id, { title: e.target.value })}
                                />
                                <textarea
                                  defaultValue={task.description}
                                  onBlur={(e) => handleUpdateTask(task.id, { description: e.target.value })}
                                />
                                <button onClick={() => setEditingTask(null)}>Cancel</button>
                              </div>
                            ) : (
                              <>
                                <div className="task-header">
                                  <h4>{task.title}</h4>
                                  <div className="task-actions">
                                    <button onClick={() => setEditingTask(task.id)} className="edit-button">✏️</button>
                                    <button onClick={() => handleDeleteTask(task.id)} className="delete-button">🗑️</button>
                                  </div>
                                </div>
                                <p>{task.description}</p>
                              </>
                            )}
                            <div className="task-meta">
                              <span className={`priority ${task.priority.toLowerCase()}`}>
                                {task.priority}
                              </span>
                              <input
                                type="text"
                                value={task.assignee || ''}
                                onChange={(e) => {
                                  const newAssignee = e.target.value;
                                  const oldAssignee = task.assignee;
                                  const tasksCopy = { ...tasks };
                                  Object.keys(tasksCopy).forEach(s => {
                                    const t = tasksCopy[s].find(t => t.id === task.id);
                                    if (t) t.assignee = newAssignee;
                                  });
                                  setTasks(tasksCopy);
                                  debouncedAssigneeChange(task.id, newAssignee, oldAssignee);
                                }}
                                placeholder="Assign to..."
                                className="assignee-input"
                              />
                            </div>
                            {task.due_date && (
                              <div className="task-due-date">
                                Due: {new Date(task.due_date).toLocaleDateString()}
                              </div>
                            )}
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </div>
          ))}
        </div>
      </div>
    </DragDropContext>
  );
};

export default Board;
