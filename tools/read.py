from pathlib import Path
from agents.project_manager import project_manager


def read_file(path):
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

    print(f"Reading: {path.relative_to(project_path)}")
    return path.read_text()