import React, { useEffect, useState } from 'react';
import api from '../api/api';
import './ProjectList.css';

const ProjectList = ({ onSelectProject }) => {
  const [projects, setProjects] = useState([]);
  const [editingProject, setEditingProject] = useState(null);
  const [showProjectForm, setShowProjectForm] = useState(false);
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
      setProjects(response.data || []);
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
      setShowProjectForm(false);
    } catch (error) {
      console.error('Error creating project:', error);
    }
  };

  const handleEditProject = async (project) => {
    try {
      const response = await api.updateProject(project.id, project);
      setProjects(projects.map(p => p.id === project.id ? response.data : p));
      setEditingProject(null);
    } catch (error) {
      console.error('Error updating project:', error);
    }
  };

  const handleDeleteProject = async (projectId, e) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Use custom styled confirmation dialog
    const confirmDelete = window.confirm('This action cannot be undone. Are you sure you want to permanently delete this project and all its tasks?');
    
    if (confirmDelete) {
      try {
        await api.deleteProject(projectId);
        setProjects(projects.filter(p => p.id !== projectId));
        // Show success feedback
        const successMessage = document.createElement('div');
        successMessage.className = 'success-message';
        successMessage.textContent = 'Project deleted successfully';
        document.body.appendChild(successMessage);
        setTimeout(() => successMessage.remove(), 3000);
      } catch (error) {
        console.error('Error deleting project:', error);
        // Show error feedback
        const errorMessage = document.createElement('div');
        errorMessage.className = 'error-message';
        errorMessage.textContent = 'Failed to delete project. Please try again.';
        document.body.appendChild(errorMessage);
        setTimeout(() => errorMessage.remove(), 3000);
      }
    }
  };

  return (
    <div className="project-list">
      <button 
        className="create-project-button"
        onClick={() => setShowProjectForm(!showProjectForm)}
      >
        {showProjectForm ? '❌ Cancel' : '➕ Create New Project'}
      </button>

      {showProjectForm && (
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
      )}

      <div className="projects">
        <h3>Your Projects</h3>
        {projects.map(project => (
          <div
            key={project.id}
            className="project-card"
            onClick={() => onSelectProject(project)}
          >
            {editingProject === project.id ? (
              <div className="project-edit-form" onClick={e => e.stopPropagation()}>
                <input
                  type="text"
                  value={project.name}
                  onChange={e => setProjects(projects.map(p => 
                    p.id === project.id ? { ...p, name: e.target.value } : p
                  ))}
                />
                <textarea
                  value={project.description || ''}
                  onChange={e => setProjects(projects.map(p => 
                    p.id === project.id ? { ...p, description: e.target.value } : p
                  ))}
                />
                <input
                  type="date"
                  value={project.deadline}
                  onChange={e => setProjects(projects.map(p => 
                    p.id === project.id ? { ...p, deadline: e.target.value } : p
                  ))}
                />
                <div className="edit-actions">
                  <button onClick={() => handleEditProject(project)}>Save</button>
                  <button onClick={() => setEditingProject(null)}>Cancel</button>
                </div>
              </div>
            ) : (
              <>
                <div className="project-content">
                  <h4>{project.name}</h4>
                  <p>{project.description}</p>
                  <span className="deadline">Due: {new Date(project.deadline).toLocaleDateString()}</span>
                </div>
                <div className="project-actions" onClick={e => e.stopPropagation()}>
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setEditingProject(project.id);
                    }}
                    className="edit-button"
                    title="Edit project"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={(e) => handleDeleteProject(project.id, e)}
                    className="delete-button"
                    title="Delete project"
                  >
                    🗑️
                  </button>
                </div>
              </>
            )}
          </div>
        ))}
      </div>

      
    </div>
  );
};

export default ProjectList;
