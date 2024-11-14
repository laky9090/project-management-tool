import React, { useState } from 'react';
import ProjectList from './components/ProjectList';
import Board from './components/Board';
import TaskForm from './components/TaskForm';

// CSS imports in correct order to match Streamlit
import './styles/variables.css';  // Base variables first
import './App.css';              // Global styles second
import './components/Board.css';  // Component styles last
import './components/TaskForm.css';

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
            <div className="board-header">
              <h2>{selectedProject.name}</h2>
            </div>
            <div className="board-container">
              <Board projectId={selectedProject.id} />
            </div>
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
