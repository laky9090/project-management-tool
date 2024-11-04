import React, { useEffect, useState } from 'react';
import api from '../api/api';
import './ProjectList.css';

const ProjectList = ({ onSelectProject }) => {
  const [projects, setProjects] = useState([]);
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    deadline: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await api.getProjects();
      setProjects(response.data);
    } catch (error) {
      console.error('Error loading projects:', error);
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    try {
      const response = await api.createProject(newProject);
      setProjects([response.data, ...projects]);
      setNewProject({
        name: '',
        description: '',
        deadline: new Date().toISOString().split('T')[0]
      });
    } catch (error) {
      console.error('Error creating project:', error);
    }
  };

  return (
    <div className="project-list">
      <form onSubmit={handleCreateProject} className="project-form">
        <h3>Create New Project</h3>
        <input
          type="text"
          value={newProject.name}
          onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
          placeholder="Project Name"
          required
        />
        <textarea
          value={newProject.description}
          onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
          placeholder="Description"
        />
        <input
          type="date"
          value={newProject.deadline}
          onChange={(e) => setNewProject({ ...newProject, deadline: e.target.value })}
        />
        <button type="submit">Create Project</button>
      </form>

      <div className="projects">
        <h3>Your Projects</h3>
        {projects.map(project => (
          <div
            key={project.id}
            className="project-card"
            onClick={() => onSelectProject(project)}
          >
            <h4>{project.name}</h4>
            <p>{project.description}</p>
            <span className="deadline">Due: {new Date(project.deadline).toLocaleDateString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProjectList;
