import React, { useEffect, useState, useCallback } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import api from '../api/api';
import './Board.css';

// Error boundary component
class DragDropErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('DragDrop error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return <div className="error-message">Error loading board. Please refresh the page.</div>;
    }
    return this.props.children;
  }
}

const Board = ({ projectId }) => {
  const [tasks, setTasks] = useState({ 'To Do': [], 'In Progress': [], 'Done': [] });
  const [error, setError] = useState(null);
  const [editingTask, setEditingTask] = useState(null);
  const [editingAssignee, setEditingAssignee] = useState(null);

  const loadTasks = useCallback(async () => {
    try {
      setError(null);
      const response = await api.getProjectTasks(projectId);
      
      const groupedTasks = response.data.reduce((acc, task) => {
        const status = task.status || 'To Do';
        if (!acc[status]) acc[status] = [];
        acc[status].push(task);
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

  const handleTaskCreated = useCallback((newTask) => {
    setTasks(prevTasks => {
      const status = newTask.status || 'To Do';
      return {
        ...prevTasks,
        [status]: [...(prevTasks[status] || []), newTask]
      };
    });
    // Force a refresh of tasks from server
    loadTasks();
  }, [loadTasks]);

  const onDragEnd = async (result) => {
    if (!result.destination) return;

    const { source, destination, draggableId } = result;
    if (source.droppableId === destination.droppableId && source.index === destination.index) return;

    try {
      setError(null);
      // Optimistically update UI
      const draggedTask = tasks[source.droppableId][source.index];
      const newTasks = { ...tasks };
      newTasks[source.droppableId] = newTasks[source.droppableId].filter((_, index) => index !== source.index);
      newTasks[destination.droppableId].splice(destination.index, 0, {
        ...draggedTask,
        status: destination.droppableId
      });
      setTasks(newTasks);

      await api.updateTaskStatus(draggableId, destination.droppableId);
    } catch (error) {
      console.error('Error updating task status:', error);
      setError('Failed to update task status. Please try again.');
      loadTasks(); // Revert to server state on error
    }
  };

  const handleUpdateTask = async (taskId, updatedData) => {
    try {
      setError(null);
      // Optimistically update UI
      setTasks(prevTasks => {
        const newTasks = { ...prevTasks };
        Object.keys(newTasks).forEach(status => {
          newTasks[status] = newTasks[status].map(task =>
            task.id === taskId ? { ...task, ...updatedData } : task
          );
        });
        return newTasks;
      });

      await api.updateTask(taskId, updatedData);
      setEditingTask(null);
    } catch (error) {
      console.error('Error updating task:', error);
      setError('Failed to update task. Please try again.');
      loadTasks(); // Revert to server state on error
    }
  };

  const handleDeleteTask = async (taskId) => {
    try {
      setError(null);
      // Optimistically update UI
      setTasks(prevTasks => {
        const newTasks = { ...prevTasks };
        Object.keys(newTasks).forEach(status => {
          newTasks[status] = newTasks[status].filter(task => task.id !== taskId);
        });
        return newTasks;
      });

      await api.deleteTask(taskId);
    } catch (error) {
      console.error('Error deleting task:', error);
      setError('Failed to delete task. Please try again.');
      loadTasks(); // Revert to server state on error
    }
  };

  const handleAssigneeChange = async (taskId, assignee) => {
    try {
      setError(null);
      // Optimistically update UI
      setTasks(prevTasks => {
        const newTasks = { ...prevTasks };
        Object.keys(newTasks).forEach(status => {
          newTasks[status] = newTasks[status].map(task =>
            task.id === taskId ? { ...task, assignee } : task
          );
        });
        return newTasks;
      });

      await api.updateTaskAssignment(taskId, assignee);
      setEditingAssignee(null);
    } catch (error) {
      console.error('Error updating task assignment:', error);
      setError('Failed to update task assignment. Please try again.');
      loadTasks(); // Revert to server state on error
    }
  };

  const renderTaskCard = (task, provided) => (
    <div
      ref={provided.innerRef}
      {...provided.draggableProps}
      {...provided.dragHandleProps}
      className="task-card"
    >
      <div className="task-header">
        {editingTask === task.id ? (
          <input
            type="text"
            defaultValue={task.title}
            className="task-title-input"
            onBlur={(e) => handleUpdateTask(task.id, { title: e.target.value })}
            autoFocus
          />
        ) : (
          <h4 className="task-title">{task.title}</h4>
        )}
        <div className="task-actions">
          <button 
            onClick={() => setEditingTask(editingTask === task.id ? null : task.id)} 
            className="edit-button"
          >
            ✏️
          </button>
          <button 
            onClick={() => handleDeleteTask(task.id)} 
            className="delete-button"
          >
            🗑️
          </button>
        </div>
      </div>

      {editingTask === task.id ? (
        <textarea
          defaultValue={task.description}
          className="task-description-input"
          onBlur={(e) => handleUpdateTask(task.id, { description: e.target.value })}
        />
      ) : (
        <p className="task-description">{task.description}</p>
      )}

      <div className="task-meta">
        <span className={`priority priority-${task.priority.toLowerCase()}`}>
          {task.priority}
        </span>
        {editingAssignee === task.id ? (
          <input
            type="text"
            className="assignee-input"
            defaultValue={task.assignee || ''}
            placeholder="Assign to..."
            onBlur={(e) => handleAssigneeChange(task.id, e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleAssigneeChange(task.id, e.target.value);
              }
            }}
            autoFocus
          />
        ) : (
          <span 
            className="assignee" 
            onClick={() => setEditingAssignee(task.id)}
            title="Click to assign"
          >
            {task.assignee || 'Click to assign'}
          </span>
        )}
      </div>

      {task.due_date && (
        <div className="due-date">
          Due: {new Date(task.due_date).toLocaleDateString('fr-FR', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric' 
          })}
        </div>
      )}
    </div>
  );

  return (
    <DragDropErrorBoundary>
      <DragDropContext onDragEnd={onDragEnd}>
        <div className="board">
          {error && <div className="error-message">{error}</div>}
          <div className="board-columns">
            {Object.entries(tasks).map(([status, statusTasks]) => (
              <div key={status} className="column">
                <h3>{status}</h3>
                <Droppable droppableId={status} type="task">
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
                          {(provided) => renderTaskCard(task, provided)}
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
    </DragDropErrorBoundary>
  );
};

export default Board;