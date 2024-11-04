import React, { useState } from 'react';
import ProjectList from './components/ProjectList';
import Board from './components/Board';
import TaskForm from './components/TaskForm';
import './App.css';

function App() {
  const [selectedProject, setSelectedProject] = useState(null);

  return (
    <div className="app">
      <div className="sidebar">
        <h1>Project Management</h1>
        <ProjectList onSelectProject={setSelectedProject} />
      </div>
      <div className="main-content">
        {selectedProject ? (
          <>
            <TaskForm projectId={selectedProject.id} />
            <Board projectId={selectedProject.id} />
          </>
        ) : (
          <div className="no-project">
            <h2>Select a project to get started</h2>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
