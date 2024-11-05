import React, { useState, useEffect } from 'react';
import api from '../api/api';

const TestTaskCreation = ({ projectId }) => {
  const [lastCreatedTask, setLastCreatedTask] = useState(null);
  const [error, setError] = useState(null);

  const createTestTask = async () => {
    try {
      setError(null);
      const testTask = {
        project_id: projectId,
        title: 'Test Task ' + new Date().toISOString(),
        description: 'Test Description',
        status: 'To Do',
        priority: 'Medium',
        assignee: 'Test User',
        due_date: new Date().toISOString().split('T')[0]
      };

      console.log('Sending test task:', testTask);
      const response = await api.createTask(testTask);
      console.log('Response:', response);
      setLastCreatedTask(response.data);
    } catch (err) {
      console.error('Test creation failed:', err);
      setError(err.response?.data?.error || err.message);
    }
  };

  return (
    <div>
      <button onClick={createTestTask}>Create Test Task</button>
      {error && <div style={{color: 'red'}}>Error: {error}</div>}
      {lastCreatedTask && (
        <div>
          <h4>Last Created Task:</h4>
          <pre>{JSON.stringify(lastCreatedTask, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default TestTaskCreation;
