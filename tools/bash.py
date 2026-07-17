import subprocess
from agents.project_manager import project_manager


def run_command(command):
    try:
        workspace_dir = project_manager.active_project_path

        if workspace_dir is None:
            return {
                "success": False,
                "stdout": "",
                "stderr": "No active project",
                "returncode": 1
            }

        process = subprocess.Popen(
            command,
            shell=True,
            cwd=str(workspace_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        output = []

        try:
            for line in process.stdout:
                print(line, end="")
                output.append(line)

            process.wait(timeout=120)

        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "success": False,
                "stdout": "".join(output)[-5000:],
                "stderr": "Command timed out after 120 seconds",
                "returncode": 1
            }

        stdout_text = "".join(output)

        return {
            "success": process.returncode == 0,
            "stdout": stdout_text[-5000:],
            "stderr": "",
            "returncode": process.returncode
        }

    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": 1
        }