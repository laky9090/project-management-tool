import React, { useEffect, useState } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import api from '../api/api';
import TestTaskCreation from './TestTaskCreation';
import './Board.css';

const Board = ({ projectId }) => {
  const [tasks, setTasks] = useState({ 'To Do': [], 'In Progress': [], 'Done': [] });

  useEffect(() => {
    loadTasks();
  }, [projectId]);

  const loadTasks = async () => {
    try {
      const response = await api.getProjectTasks(projectId);
      const groupedTasks = response.data.reduce((acc, task) => {
        if (!acc[task.status]) acc[task.status] = [];
        acc[task.status].push(task);
        return acc;
      }, { 'To Do': [], 'In Progress': [], 'Done': [] });
      setTasks(groupedTasks);
    } catch (error) {
      console.error('Error loading tasks:', error);
    }
  };

  const onDragEnd = async (result) => {
    if (!result.destination) return;

    const { source, destination, draggableId } = result;
    if (source.droppableId === destination.droppableId) return;

    try {
      await api.updateTaskStatus(draggableId, destination.droppableId);
      await loadTasks();
    } catch (error) {
      console.error('Error updating task status:', error);
    }
  };

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="board">
        <TestTaskCreation projectId={projectId} />
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
                            <span>{task.assignee}</span>
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
    </DragDropContext>
  );
};

export default Board;
