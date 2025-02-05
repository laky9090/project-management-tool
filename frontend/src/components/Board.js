import React, { useEffect, useState, useCallback } from "react";
import TaskForm from "./TaskForm";
import api from "../api/api";
import "./Board.css";
import "./task.css";

const Board = ({ projectId }) => {
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState(null);
  const [dateValidationError, setDateValidationError] = useState(null);
  const [editingTask, setEditingTask] = useState(null);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [sortConfig, setSortConfig] = useState({
    key: "created_at",
    direction: "desc",
  });
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [isValidating, setIsValidating] = useState(false);

  const validateDates = (startDate, endDate) => {
    if (new Date(startDate) > new Date(endDate)) {
      setDateValidationError("Start date cannot be later than end date");
      return false;
    }
    return true;
  };

  const handleDateValidation = (startDate, endDate) => {
    if (isValidating) return;
    setIsValidating(true);

    if (!validateDates(startDate, endDate)) {
      setTimeout(() => setIsValidating(false), 300);
      return false;
    }

    setIsValidating(false);
    return true;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const isPastDue = date < today;
    const formattedDate = date.toLocaleDateString("fr-FR");
    return { formattedDate, isPastDue };
  };

  const parseDate = (dateStr) => {
    if (!dateStr) return null;
    if (!dateStr.includes("/")) return dateStr;
    const [day, month, year] = dateStr.split("/");
    return `${year}-${month}-${day}`;
  };

  const validateDate = (dateStr) => {
    if (!dateStr) return true;
    const date = new Date(dateStr);
    return date instanceof Date && !isNaN(date);
  };

  const loadTasks = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const response = await api.getProjectTasks(projectId);
      setTasks(response.data);
    } catch (error) {
      console.error("Error loading tasks:", error);
      setError("Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const handleUpdateTask = async (taskId, updatedData) => {
    try {
      if (updating) return;
      setUpdating(true);
      setError(null);

      if (updatedData.due_date) {
        if (!validateDate(updatedData.due_date)) {
          throw new Error("Invalid date format");
        }
        updatedData.due_date = parseDate(updatedData.due_date);
      }

      const response = await api.updateTask(taskId, updatedData);
      if (response.data) {
        await loadTasks();
      }
      return true;
    } catch (error) {
      console.error("Error updating task:", error);
      setError("Failed to update task. Please try again.");
      return false;
    } finally {
      setUpdating(false);
    }
  };

  const handleCommentEdit = async (taskId, currentValue) => {
    const cell = document.querySelector(
      `td[data-task-id="${taskId}"][data-field="comment"]`,
    );
    if (!cell) return;

    const textarea = document.createElement("textarea");
    textarea.value = currentValue || "";
    textarea.style.width = "100%";
    textarea.style.minHeight = "100px";
    textarea.style.resize = "vertical";

    const originalContent = cell.innerHTML;
    cell.innerHTML = "";
    cell.appendChild(textarea);
    textarea.focus();

    const handleBlur = async () => {
      try {
        const newValue = textarea.value.trim();
        if (newValue !== currentValue) {
          const success = await handleUpdateTask(taskId, { comment: newValue });
          if (!success) {
            cell.innerHTML = originalContent;
          }
        } else {
          cell.innerHTML = originalContent;
        }
      } catch (error) {
        cell.innerHTML = originalContent;
        setError("Failed to update comment. Please try again.");
      }
      textarea.removeEventListener("blur", handleBlur);
    };

    textarea.addEventListener("blur", handleBlur);
  };

  const handleDateEdit = async (taskId, currentValue, field) => {
    const cell = document.querySelector(
      `td[data-task-id="${taskId}"][data-field="${field}"]`,
    );
    if (!cell) return;

    const task = tasks.find((t) => t.id === taskId);
    if (!task) return;

    const existingPopup = document.querySelector(".calendar-popup");
    if (existingPopup) {
      existingPopup.remove();
    }

    const popup = document.createElement("div");
    popup.className = "calendar-popup";

    const calendar = document.createElement("input");
    calendar.type = "date";

    if (currentValue) {
      const [day, month, year] = currentValue.split("/");
      calendar.value = `${year}-${month}-${day}`;
    }

    popup.appendChild(calendar);

    const cellRect = cell.getBoundingClientRect();
    popup.style.position = "absolute";
    popup.style.top = `${cellRect.bottom + window.scrollY}px`;
    popup.style.left = `${cellRect.left + window.scrollX}px`;

    document.body.appendChild(popup);
    calendar.focus();

    const handleChange = async () => {
      try {
        if (calendar.value) {
          const newDate = new Date(calendar.value);
          const updatedDates = {
            start_date:
              field === "start_date" ? calendar.value : task.start_date,
            end_date: field === "end_date" ? calendar.value : task.end_date,
          };

          if (
            !handleDateValidation(
              updatedDates.start_date,
              updatedDates.end_date,
            )
          ) {
            cell.textContent = currentValue || "";
            popup.remove();
            return;
          }

          const formattedDate = newDate.toLocaleDateString("fr-FR");
          if (formattedDate !== currentValue) {
            const success = await handleUpdateTask(taskId, {
              [field]: calendar.value,
            });
            if (!success) {
              cell.textContent = currentValue || "";
            }
          }
        } else {
          const success = await handleUpdateTask(taskId, { [field]: null });
          if (!success) {
            cell.textContent = currentValue || "";
          }
        }
      } catch (error) {
        console.error("Error updating date:", error);
        cell.textContent = currentValue || "";
      } finally {
        popup.remove();
      }
    };

    const handleClickOutside = (event) => {
      if (!popup.contains(event.target) && event.target !== cell) {
        handleChange();
        document.removeEventListener("click", handleClickOutside);
      }
    };

    setTimeout(() => {
      document.addEventListener("click", handleClickOutside);
    }, 0);

    calendar.addEventListener("change", handleChange);
  };

  const handleExportTasks = async () => {
    try {
      setError(null);
      await api.exportProjectTasks(projectId);
    } catch (error) {
      console.error("Error exporting tasks:", error);
      setError("Failed to export tasks. Please try again.");
    }
  };

  const handleTaskCreated = useCallback(
    (newTask) => {
      setTasks((prevTasks) => [newTask, ...prevTasks]);
      setShowTaskForm(false);
      loadTasks();
    },
    [loadTasks],
  );

  const handleDeleteTask = async (taskId) => {
    try {
      setError(null);
      if (
        window.confirm(
          "Are you sure you want to delete this task? This action cannot be undone.",
        )
      ) {
        await api.deleteTask(taskId);
        setTasks(tasks.filter((task) => task.id !== taskId));
      }
    } catch (error) {
      console.error("Error deleting task:", error);
      setError("Failed to delete task. Please try again.");
    }
  };

  const handleDuplicateTask = async (taskId) => {
    try {
      setError(null);
      const response = await api.duplicateTask(taskId);
      if (response.data) {
        await loadTasks();
      }
    } catch (error) {
      console.error("Error duplicating task:", error);
      setError("Failed to duplicate task. Please try again.");
    }
  };

  const handleSort = (key) => {
    setSortConfig((prevConfig) => ({
      key,
      direction:
        prevConfig.key === key && prevConfig.direction === "asc"
          ? "desc"
          : "asc",
    }));
  };

  const handleAssigneeEdit = async (taskId, currentValue) => {
    try {
      setError(null);
      const cell = document.querySelector(
        `td[data-task-id="${taskId}"][data-field="assignee"]`,
      );
      if (!cell) return;

      const input = document.createElement("input");
      input.type = "text";
      input.value = currentValue || "";
      input.style.width = "100%";
      input.style.textAlign = "center";
      input.placeholder = "Enter assignee name";

      const originalContent = cell.innerHTML;
      cell.innerHTML = "";
      cell.appendChild(input);
      input.focus();

      const handleUpdate = async () => {
        try {
          setUpdating(true);
          const newValue = input.value;
          const assigneeValue =
            !newValue || newValue.trim() === "" ? null : newValue.trim();

          const response = await api.updateTask(taskId, {
            assignee: assigneeValue,
          });

          if (response.data) {
            setTasks((prevTasks) =>
              prevTasks.map((task) =>
                task.id === taskId
                  ? { ...task, assignee: response.data.assignee }
                  : task,
              ),
            );
            cell.textContent = response.data.assignee || "Unassigned";
          } else {
            cell.innerHTML = originalContent;
            setError("Failed to update assignee");
          }
        } catch (error) {
          console.error("Error updating assignee:", error);
          cell.innerHTML = originalContent;
          const errorMessage =
            error.response?.data?.error ||
            "Failed to update assignee. Please try again.";
          setError(errorMessage);
        } finally {
          setUpdating(false);
        }
      };

      input.addEventListener("blur", handleUpdate);
      input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
          input.blur();
        }
      });
    } catch (error) {
      console.error("Error setting up assignee edit:", error);
      setError("Failed to initialize assignee editing");
    }
  };

  const handleUndoTask = async (taskId) => {
    try {
      setError(null);
      setUpdating(true);
      const response = await api.undoTaskChange(taskId);
      if (response.data) {
        await loadTasks();
      }
    } catch (error) {
      console.error("Error undoing task change:", error);
      setError("Failed to undo task change. Please try again.");
    } finally {
      setUpdating(false);
    }
  };

  const sortedTasks = [...tasks].sort((a, b) => {
    if (a[sortConfig.key] < b[sortConfig.key]) {
      return sortConfig.direction === "asc" ? -1 : 1;
    }
    if (a[sortConfig.key] > b[sortConfig.key]) {
      return sortConfig.direction === "asc" ? 1 : -1;
    }
    return 0;
  });

  const getSortIcon = (key) => {
    if (sortConfig.key === key) {
      return sortConfig.direction === "asc" ? " ↑" : " ↓";
    }
    return " ↕";
  };

  if (loading) {
    return <div className="loading">Loading tasks...</div>;
  }

  return (
    <div className="board">
      {dateValidationError && (
        <div className="date-validation-overlay">
          <div className="date-validation-dialog">
            <p>{dateValidationError}</p>
            <div className="date-validation-buttons">
              <button
                className="date-validation-ok"
                onClick={() => setDateValidationError(null)}
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
      {error && <div className="error-message">{error}</div>}
      {updating && <div className="loading">Updating task...</div>}

      <div className="board-actions">
        <button
          className="add-task-button"
          onClick={() => setShowTaskForm(true)}
        >
          ➕ Add New Task
        </button>
        <button className="export-button" onClick={handleExportTasks}>
          📥 Export to Excel
        </button>
      </div>

      {showTaskForm && (
        <TaskForm
          projectId={projectId}
          onTaskCreated={handleTaskCreated}
          onCancel={() => setShowTaskForm(false)}
        />
      )}

      <div className="table-container">
        <table className="task-table">
          <thead>
            <tr>
              <th onClick={() => handleSort("title")}>
                Title {getSortIcon("title")}
              </th>
              <th onClick={() => handleSort("comment")}>
                Notes {getSortIcon("comment")}
              </th>
              <th onClick={() => handleSort("status")}>
                Status {getSortIcon("status")}
              </th>
              <th onClick={() => handleSort("priority")}>
                Priority {getSortIcon("priority")}
              </th>
              <th
                onClick={() => handleSort("start_date")}
                className="date-column"
              >
                Start Date {getSortIcon("start_date")}
              </th>
              <th
                onClick={() => handleSort("end_date")}
                className="date-column"
              >
                End Date {getSortIcon("end_date")}
              </th>
              <th
                onClick={() => handleSort("updated_at")}
                className="date-column"
              >
                Last Update {getSortIcon("updated_at")}
              </th>
              <th onClick={() => handleSort("assignee")}>
                Assigned To {getSortIcon("assignee")}
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedTasks.map((task) => (
              <tr key={task.id} data-status={task.status}>
                <td
                  onClick={() => setEditingTask(task.id)}
                  data-task-id={task.id}
                  data-field="title"
                >
                  {editingTask === task.id ? (
                    <input
                      type="text"
                      defaultValue={task.title}
                      onBlur={(e) => {
                        const newValue = e.target.value.trim();
                        if (newValue !== task.title) {
                          handleUpdateTask(task.id, { title: newValue });
                        }
                        setEditingTask(null);
                      }}
                      onKeyPress={(e) => {
                        if (e.key === "Enter") {
                          e.target.blur();
                        }
                      }}
                      autoFocus
                    />
                  ) : (
                    task.title
                  )}
                </td>
                <td
                  className="notes-cell"
                  onClick={() => handleCommentEdit(task.id, task.comment)}
                  data-task-id={task.id}
                  data-field="comment"
                >
                  <div className="notes-content">
                    {task.comment || ""}
                  </div>
                </td>
                <td>
                  <select
                    value={task.status}
                    onChange={(e) =>
                      handleUpdateTask(task.id, { status: e.target.value })
                    }
                  >
                    <option value="To Do">To Do</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Done">Done</option>
                    <option value="Canceled">Canceled</option>
                  </select>
                </td>
                <td data-priority={task.priority}>
                  <select
                    value={task.priority}
                    onChange={(e) =>
                      handleUpdateTask(task.id, { priority: e.target.value })
                    }
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </td>
                <td
                  className="date-column"
                  onClick={() =>
                    handleDateEdit(
                      task.id,
                      formatDate(task.start_date).formattedDate,
                      "start_date",
                    )
                  }
                  data-task-id={task.id}
                  data-field="start_date"
                >
                  {formatDate(task.start_date).formattedDate}
                </td>
                <td
                  className={`date-column ${formatDate(task.end_date).isPastDue ? "past-due" : ""}`}
                  onClick={() =>
                    handleDateEdit(
                      task.id,
                      formatDate(task.end_date).formattedDate,
                      "end_date",
                    )
                  }
                  data-task-id={task.id}
                  data-field="end_date"
                >
                  {formatDate(task.end_date).formattedDate}
                </td>
                <td className="date-column">
                  {formatDate(task.updated_at).formattedDate}
                </td>
                <td
                  onClick={() => handleAssigneeEdit(task.id, task.assignee)}
                  data-task-id={task.id}
                  data-field="assignee"
                >
                  {task.assignee || "Unassigned"}
                </td>
                <td className="actions-column">
                  <button
                    onClick={() =>
                      setEditingTask(editingTask === task.id ? null : task.id)
                    }
                    className="edit-button"
                    title="Edit"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={() => handleDuplicateTask(task.id)}
                    className="duplicate-button"
                    title="Duplicate"
                  >
                    📋
                  </button>
                  <button
                    onClick={() => handleUndoTask(task.id)}
                    className="undo-button"
                    title="Undo last change"
                  >
                    ↩️
                  </button>
                  <button
                    onClick={() => handleDeleteTask(task.id)}
                    className="delete-button"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Board;