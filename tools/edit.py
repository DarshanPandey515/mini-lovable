from pathlib import Path
from agents.project_manager import project_manager


def edit_file(path, old_text, new_text):
    if isinstance(path, str):
        path = Path(path)

    project_path = project_manager.active_project_path
    if project_path is None:
        raise ValueError("No active project. Please create a project first.")

    if not path.is_absolute():
        path = project_path / path

    try:
        path.relative_to(project_path)
    except ValueError:
        raise ValueError(f"Access denied: {path} is outside the project workspace")

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise IsADirectoryError(f"Path is a directory: {path}")

    content = path.read_text()

    if old_text not in content:
        return {
            "success": False,
            "error": f"Text not found in {path.relative_to(project_path)}"
        }

    updated = content.replace(old_text, new_text, 1)
    path.write_text(updated)

    print(f"Edited: {path.relative_to(project_path)}")

    return {
        "success": True,
        "path": str(path.relative_to(project_path)),
        "content_edited": new_text[:100] + "..." if len(new_text) > 100 else new_text
    }