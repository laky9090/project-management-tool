import React, { useEffect, useState } from 'react';
import api from '../api/api';
import './ProjectList.css';

const ProjectList = ({ onSelectProject }) => {
  const [projects, setProjects] = useState([]);
  const [deletedProjects, setDeletedProjects] = useState([]);
  const [editingProject, setEditingProject] = useState(null);
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    deadline: new Date().toISOString().split('T')[0]
  });
  const [showDeletedProjects, setShowDeletedProjects] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const [activeResponse, deletedResponse] = await Promise.all([
        api.getProjects(),
        api.getDeletedProjects()
      ]);
      setProjects(activeResponse.data || []);
      setDeletedProjects(Array.isArray(deletedResponse.data) ? deletedResponse.data : []);
    } catch (error) {
      console.error('Error loading projects:', error);
      setDeletedProjects([]);
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
    try {
      await api.deleteProject(projectId);
      const deletedProject = projects.find(p => p.id === projectId);
      setProjects(projects.filter(p => p.id !== projectId));
      setDeletedProjects([...deletedProjects, { ...deletedProject, deleted_at: new Date() }]);
    } catch (error) {
      console.error('Error deleting project:', error);
    }
  };

  const handleRestoreProject = async (projectId, e) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await api.restoreProject(projectId);
      setDeletedProjects(deletedProjects.filter(p => p.id !== projectId));
      loadProjects(); // Reload active projects
    } catch (error) {
      console.error('Error restoring project:', error);
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

      {deletedProjects.length > 0 && (
        <div className="deleted-projects">
          <div 
            className="deleted-projects-header"
            onClick={() => setShowDeletedProjects(!showDeletedProjects)}
          >
            <h3>
              Deleted Projects ({deletedProjects.length})
              <span className={`toggle-icon ${showDeletedProjects ? 'expanded' : ''}`}>
                ▼
              </span>
            </h3>
          </div>
          <div className={`deleted-projects-content ${showDeletedProjects ? 'expanded' : ''}`}>
            {deletedProjects.map(project => (
              <div key={project.id} className="project-card deleted">
                <div className="project-content">
                  <h4>{project.name}</h4>
                  <p>{project.description}</p>
                  <span className="deadline">
                    Deleted: {new Date(project.deleted_at).toLocaleDateString('fr-FR')}
                  </span>
                </div>
                <div className="project-actions">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRestoreProject(project.id);
                    }}
                    className="restore-button"
                    title="Restore project"
                  >
                    🔄
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectList;