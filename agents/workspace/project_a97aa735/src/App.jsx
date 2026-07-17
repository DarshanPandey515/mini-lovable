import { useState, useEffect } from "react";
import TodoItem from "./components/TodoItem";

const FILTERS = {
  ALL: "all",
  ACTIVE: "active",
  COMPLETED: "completed",
};

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [newTask, setNewTask] = useState("");
  const [filter, setFilter] = useState(FILTERS.ALL);

  // Load from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("todo-tasks");
    if (stored) setTasks(JSON.parse(stored));
  }, []);

  // Persist to localStorage
  useEffect(() => {
    localStorage.setItem("todo-tasks", JSON.stringify(tasks));
  }, [tasks]);

  const addTask = () => {
    const trimmed = newTask.trim();
    if (!trimmed) return;
    setTasks([
      ...tasks,
      { id: Date.now(), text: trimmed, completed: false },
    ]);
    setNewTask("");
  };

  const toggleComplete = (id) => {
    setTasks(
      tasks.map((t) =>
        t.id === id ? { ...t, completed: !t.completed } : t
      )
    );
  };

  const deleteTask = (id) => {
    setTasks(tasks.filter((t) => t.id !== id));
  };

  const editTask = (id, newText) => {
    setTasks(
      tasks.map((t) =>
        t.id === id ? { ...t, text: newText } : t
      )
    );
  };

  const clearCompleted = () => {
    setTasks(tasks.filter((t) => !t.completed));
  };

  const filteredTasks = tasks.filter((t) => {
    if (filter === FILTERS.ACTIVE) return !t.completed;
    if (filter === FILTERS.COMPLETED) return t.completed;
    return true;
  });

  const handleKeyPress = (e) => {
    if (e.key === "Enter") addTask();
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-4">
      <nav className="w-full bg-blue-600 text-white p-4 mb-4">
        <h1 className="text-xl font-semibold text-center">Todo App</h1>
      </nav>
      <div className="bg-white rounded-lg shadow w-full max-w-md p-6">
        <h1 className="text-2xl font-bold mb-4 text-center">Todo</h1>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            className="flex-1 border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="What needs to be done?"
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button
            onClick={addTask}
            className="bg-blue-500 text-white rounded px-4 py-2 hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Add
          </button>
        </div>
        {tasks.length === 0 ? (
          <p className="text-center text-gray-500">No tasks yet.</p>
        ) : (
          <ul className="space-y-2">
            {filteredTasks.map((task) => (
              <TodoItem
                key={task.id}
                task={task}
                onToggle={() => toggleComplete(task.id)}
                onDelete={() => deleteTask(task.id)}
                onEdit={(newText) => editTask(task.id, newText)}
              />
            ))}
          </ul>
        )}
        {tasks.length > 0 && (
          <div className="flex justify-between items-center mt-4">
            <div className="flex gap-2">
              <button
                onClick={() => setFilter(FILTERS.ALL)}
                className={`px-2 py-1 rounded ${filter===FILTERS.ALL?"bg-gray-300":"bg-gray-100"}`}
              >
                All
              </button>
              <button
                onClick={() => setFilter(FILTERS.ACTIVE)}
                className={`px-2 py-1 rounded ${filter===FILTERS.ACTIVE?"bg-gray-300":"bg-gray-100"}`}
              >
                Active
              </button>
              <button
                onClick={() => setFilter(FILTERS.COMPLETED)}
                className={`px-2 py-1 rounded ${filter===FILTERS.COMPLETED?"bg-gray-300":"bg-gray-100"}`}
              >
                Completed
              </button>
            </div>
            <button
              onClick={clearCompleted}
              className="text-sm text-red-500 hover:underline"
            >
              Clear completed
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
