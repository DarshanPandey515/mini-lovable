import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

BASE_WORKSPACE = Path(
    os.getenv("WORKSPACE_DIR") or (Path(__file__).parent / "workspace")
)


class ProjectManager:

    def __init__(self):
        BASE_WORKSPACE.mkdir(parents=True, exist_ok=True)
        self.active_project_id: Optional[str] = None
        self.active_project_path: Optional[Path] = None

    def create_project(self) -> str:
        project_id = str(uuid.uuid4())[:8]
        project_path = BASE_WORKSPACE / f"project_{project_id}"
        project_path.mkdir(parents=True, exist_ok=True)

        self.active_project_id = project_id
        self.active_project_path = project_path

        print(f"Created project: project_{project_id} at {project_path}")
        return project_id

    def get_project_path(self, project_id: Optional[str] = None) -> Path:
        if project_id is None:
            project_id = self.active_project_id

        if project_id is None:
            raise ValueError("No active project. Create one first.")

        project_path = BASE_WORKSPACE / f"project_{project_id}"
        if not project_path.exists():
            raise FileNotFoundError(f"Project {project_id} not found")

        return project_path

    def set_active_project(self, project_id: str):
        project_path = self.get_project_path(project_id)
        self.active_project_id = project_id
        self.active_project_path = project_path
        print(f"Switched to project: project_{project_id}")

    def delete_project(self, project_id: Optional[str] = None):
        project_path = self.get_project_path(project_id)
        shutil.rmtree(project_path)

        if project_id == self.active_project_id:
            self.active_project_id = None
            self.active_project_path = None

        print(f"Deleted project: project_{project_id}")

    def list_projects(self) -> list:
        projects = []
        for item in BASE_WORKSPACE.iterdir():
            if item.is_dir() and item.name.startswith("project_"):
                project_id = item.name.replace("project_", "")
                file_count = sum(1 for _ in item.rglob("*") if _.is_file())
                projects.append({
                    "id": project_id,
                    "path": str(item),
                    "files": file_count,
                    "exists": True
                })
        return projects

    def get_active_project_info(self) -> dict:
        if self.active_project_id is None:
            return {"active": False}

        return {
            "active": True,
            "id": self.active_project_id,
            "path": str(self.active_project_path),
            "files": sum(1 for _ in self.active_project_path.rglob("*") if _.is_file())
        }


project_manager = ProjectManager()