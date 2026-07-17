import { useState } from "react";

export default function TodoItem({ task, onToggle, onDelete, onEdit }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(task.text);

  const handleSave = () => {
    const trimmed = editText.trim();
    if (trimmed) onEdit(trimmed);
    setIsEditing(false);
  };

  return (
    <li className="flex items-center justify-between bg-gray-50 rounded p-2">
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={task.completed}
          onChange={onToggle}
          className="form-checkbox h-4 w-4 text-blue-600"
        />
        {isEditing ? (
          <input
            type="text"
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSave()}
            className="border-b border-gray-300 focus:outline-none focus:border-blue-500"
          />
        ) : (
          <span
            className={`${
              task.completed ? "line-through text-gray-500" : ""
            }`}
          >
            {task.text}
          </span>
        )}
      </div>
      <div className="flex gap-2 items-center">
        {isEditing ? (
          <button
            onClick={handleSave}
            className="text-sm text-green-600 hover:underline"
          >
            Save
          </button>
        ) : (
          <button
            onClick={() => setIsEditing(true)}
            className="text-sm text-blue-600 hover:underline"
          >
            Edit
          </button>
        )}
        <button
          onClick={onDelete}
          className="text-sm text-red-600 hover:underline"
        >
          Delete
        </button>
      </div>
    </li>
  );
}
