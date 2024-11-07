import React, { useEffect, useState } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import api from '../api/api';
import './Board.css';

const Board = ({ projectId }) => {
  const [tasks, setTasks] = useState({ 'To Do': [], 'In Progress': [], 'Done': [] });
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTasks();
  }, [projectId]);

  const loadTasks = async () => {
    try {
      setError(null);
      console.log('Loading tasks for project:', projectId);
      const response = await api.getProjectTasks(projectId);
      console.log('Loaded tasks:', response.data);
      
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
  };

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

  const handleAssigneeChange = async (taskId, assignee) => {
    try {
      setError(null);
      console.log('Updating task assignment:', { taskId, assignee });
      await api.updateTaskAssignment(taskId, assignee);
      await loadTasks();
    } catch (error) {
      console.error('Error updating task assignment:', error);
      setError('Failed to update task assignment. Please try again.');
    }
  };

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
                            <h4>{task.title}</h4>
                            <p>{task.description}</p>
                            <div className="task-meta">
                              <span className={`priority ${task.priority.toLowerCase()}`}>
                                {task.priority}
                              </span>
                              <input
                                type="text"
                                value={task.assignee || ''}
                                onChange={(e) => handleAssigneeChange(task.id, e.target.value)}
                                placeholder="Assign to..."
                                className="assignee-input"
                              />
                            </div>
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
