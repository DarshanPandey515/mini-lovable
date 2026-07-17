from pathlib import Path
from agents.project_manager import project_manager


def write_file(path, content):
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

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content or "")

    print(f"Wrote: {path.relative_to(project_path)}")

    return {
        "success": True,
        "path": str(path.relative_to(project_path)),
        "content_preview": content[:200] + "..." if content and len(content) > 200 else content
    }