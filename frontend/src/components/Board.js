import React, { useEffect, useState, useCallback } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import api from '../api/api';
import './Board.css';

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

  const handleAssigneeChange = async (taskId, assignee) => {
    try {
      setError(null);
      await api.updateTaskAssignment(taskId, assignee);
      await loadTasks();
      setEditingAssignee(null);
    } catch (error) {
      console.error('Error updating task assignment:', error);
      setError('Failed to update task assignment. Please try again.');
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
  );
};

export default Board;
