import functools
import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.capabilities import ProcessHistory
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError, UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits

from tools import run_command, read_file, write_file, edit_file
from .system import FIXER_SYSTEM_PROMPT
from .llm import MODEL
from .project_manager import project_manager
from .planner import run_planner
from .codegen import run_codegen
from .state import (
    add_conversation_message,
    update_conversation_status,
    update_todos,
)

logger = logging.getLogger(__name__)

MAX_FIXER_STEPS = 8

MAX_HISTORY_MESSAGES = 10

MAX_RUN_ATTEMPTS = 3
RUN_RETRY_BACKOFF_SECONDS = 5


def trim_history(messages: list[ModelMessage], max_recent_messages: int) -> list[ModelMessage]:
    if len(messages) <= max_recent_messages + 1:
        return messages

    first = messages[0]
    start_idx = len(messages) - max_recent_messages

    while start_idx > 1:
        candidate = messages[start_idx]
        if isinstance(candidate, ModelRequest):
            tool_return_ids = {
                p.tool_call_id for p in candidate.parts
                if isinstance(p, ToolReturnPart)
            }
            if tool_return_ids:
                prev = messages[start_idx - 1]
                prev_call_ids = (
                    {p.tool_call_id for p in prev.parts if isinstance(p, ToolCallPart)}
                    if isinstance(prev, ModelResponse) else set()
                )
                if tool_return_ids - prev_call_ids:
                    start_idx -= 1
                    continue
        break

    return [first] + messages[start_idx:]


@dataclass
class FixDeps:
    notify: Callable[[str, dict], None]
    conversation_id: Optional[str] = None
    step: int = 0


fixer_agent = Agent(
    MODEL,
    deps_type=FixDeps,
    system_prompt=FIXER_SYSTEM_PROMPT,
    output_type=str,
    retries=2,
    # This call goes through pydantic-ai directly rather than
    # structured_completion() (see llm.py), so it had no explicit token cap
    # at all - equally exposed to the account's 8000 TPM ceiling once
    # several fixer turns land in the same rolling minute as the
    # planner/codegen calls that kicked off the build.
    model_settings=ModelSettings(max_tokens=2048),
    capabilities=[
        ProcessHistory(
            processor=functools.partial(trim_history, max_recent_messages=MAX_HISTORY_MESSAGES)
        )
    ],
)


def _note_step(deps: FixDeps, message: str, tool_call: str) -> None:
    deps.step += 1
    deps.notify("status", {"type": "executing", "message": f"Step {deps.step}: {message}"})
    if deps.conversation_id:
        add_conversation_message(
            deps.conversation_id, "assistant", message,
            message_type="tool_call", tool_call=tool_call, hidden=True,
        )


@fixer_agent.tool
def read(ctx: RunContext[FixDeps], path: str) -> str:
    _note_step(ctx.deps, f"Reading: {path}", tool_call="read")
    try:
        return read_file(path)
    except Exception as e:
        raise ModelRetry(str(e))


@fixer_agent.tool
def write(ctx: RunContext[FixDeps], path: str, content: str) -> str:
    _note_step(ctx.deps, f"Writing: {path}", tool_call="write")
    try:
        write_file(path, content)
    except Exception as e:
        raise ModelRetry(str(e))
    return f"Wrote {path} successfully."


@fixer_agent.tool
def edit(ctx: RunContext[FixDeps], path: str, old_text: str, new_text: str) -> str:
    """Replace one exact snippet of text in an existing file with new text.

    Args:
        path: Path to the file, relative to the project root.
        old_text: The exact existing text to find (must match exactly, including whitespace).
        new_text: The text to replace it with.
    """
    _note_step(ctx.deps, f"Editing: {path}", tool_call="edit")
    try:
        result = edit_file(path, old_text, new_text)
    except Exception as e:
        raise ModelRetry(str(e))
    if not result.get("success", True):
        raise ModelRetry(result.get("error", "old_text not found in file"))
    return f"Edited {path} successfully."


@fixer_agent.tool
def bash(ctx: RunContext[FixDeps], command: str) -> dict:
    """Run a shell command in the project's root directory (e.g. npm run build).

    Args:
        command: The shell command to run.
    """
    _note_step(ctx.deps, f"Running: {command}", tool_call="bash")
    return run_command(command)


def _is_daily_quota_error(e: Exception) -> bool:
    """Groq's per-minute (TPM) limits recover within seconds and are worth
    retrying. Per-day (TPD) limits don't recover until the next day - a
    retry loop against that error just wastes more of an already-exhausted
    budget, so it needs to be detected and treated as fatal, not transient."""
    text = str(e).lower()
    return "tpd" in text or "per day" in text or "tokens per day" in text


def _is_transient_api_error(e: Exception) -> bool:
    if isinstance(e, ModelAPIError):
        return not _is_daily_quota_error(e)
    if isinstance(e, ModelHTTPError):
        # Rate-limit HTTP errors (429) are only worth retrying if they're not
        # the daily quota - a 429 body can carry either TPM or TPD.
        return e.status_code == 429 and not _is_daily_quota_error(e)
    return False


VITE_CONFIG_CONTENT = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
"""


def scaffold_project() -> dict:
    """Deterministic project setup - no LLM call needed for this, it's the
    same fixed commands on every build, so there's no reason to spend a
    request (and its retry budget) on the model deciding to run them.

    Installs everything the generated code always assumes exists
    (react-router-dom, Tailwind v4 via its Vite plugin) and wires the
    Tailwind plugin into vite.config.js directly here, rather than leaving
    either to the model. A missing dependency isn't something the fixer
    reliably catches - it doesn't know to reach for `npm install` on a
    "cannot resolve import" error unless told to, and by the time it's
    re-reading files hoping to spot a code bug that isn't there, it's
    already burned through its step budget without ever running it.
    """
    steps = [
        "npm create vite@latest . -- --template react --no-interactive",
        "npm install",
        "npm install react-router-dom",
        "npm install tailwindcss @tailwindcss/vite",
    ]
    for cmd in steps:
        result = run_command(cmd)
        if not result.get("success", True):
            return result

    write_file("vite.config.js", VITE_CONFIG_CONTENT)
    return {"success": True}


def write_generated_files(files) -> None:
    for f in files:
        write_file(f.path, f.content)


def check_build() -> dict:
    return run_command("npm run build")


def run_fixer(instruction: str, notify: Callable[[str, dict], None], conversation_id: Optional[str] = None) -> str:
    """Bounded, tool-based correction/edit loop against whatever project is
    currently active in project_manager. Used both for post-build error
    correction and for follow-up change requests (run_followup below) -
    both are really the same task: make a small, targeted change to an
    existing codebase using read/write/edit/bash, then verify with a
    build."""
    deps = FixDeps(notify=notify, conversation_id=conversation_id)
    result = fixer_agent.run_sync(
        instruction,
        deps=deps,
        usage_limits=UsageLimits(request_limit=MAX_FIXER_STEPS),
    )
    return result.output


def run_followup(prompt: str, conversation_id: str, project_id: str, notify: Callable[[str, dict], None]) -> dict:
    """Apply a user-requested change to an already-built project. Reuses the
    fixer's read/write/edit/bash loop instead of teaching codegen to do
    incremental edits - codegen only knows how to generate a whole app from
    scratch, but the fixer is already built for exactly this: small,
    targeted changes to an existing codebase, just triggered by a feature
    request instead of a failed build."""
    update_conversation_status(conversation_id, "updating")
    add_conversation_message(conversation_id, "user", prompt)
    notify("status", {"type": "updating", "message": "Applying your change..."})

    project_manager.set_active_project(project_id)
    instruction = (
        "The app is already built and working. Apply this requested change:\n\n"
        f"{prompt}\n\n"
        "Read whatever files you need to understand the current code before "
        "editing. When done, run `npm run build` to confirm it still builds."
    )

    try:
        message = _run_with_retry(
            lambda: run_fixer(instruction, notify, conversation_id=conversation_id), notify, "followup"
        )
        success = True
    except UsageLimitExceeded:
        message = "Ran out of steps applying that change - try breaking it into something smaller."
        success = False
    except Exception as e:
        logger.error(f"Followup error: {e}", exc_info=True)
        message = f"Couldn't apply that change: {e}"
        success = False

    add_conversation_message(conversation_id, "assistant", message)
    update_conversation_status(conversation_id, "complete")

    return {
        "success": success,
        "message": message,
        "project_id": project_id,
        "project_path": str(project_manager.active_project_path),
    }


def _run_with_retry(run_fn, notify: Callable[[str, dict], None], label: str):
    """Run a single LLM call/loop with a bounded retry, but only for
    transient errors - a daily-quota error fails immediately since retrying
    it cannot succeed until quota resets."""
    last_error = None
    for attempt in range(1, MAX_RUN_ATTEMPTS + 1):
        try:
            return run_fn()
        except (ModelAPIError, ModelHTTPError) as e:
            if _is_daily_quota_error(e):
                logger.error(f"{label}: daily token quota exhausted, not retrying: {e}")
                raise
            if not _is_transient_api_error(e):
                raise
            last_error = e
            logger.warning(f"{label}: transient error on attempt {attempt}/{MAX_RUN_ATTEMPTS}: {e}")
            if attempt < MAX_RUN_ATTEMPTS:
                notify("status", {
                    "type": "retrying",
                    "message": f"{label}: API hiccup, retrying (attempt {attempt + 1}/{MAX_RUN_ATTEMPTS})..."
                })
                time.sleep(RUN_RETRY_BACKOFF_SECONDS * attempt)
    raise last_error


def run_agent(prompt, conversation_id=None, emit=None):

    def notify(event_type, data):
        if emit:
            emit(event_type, data)

    logger.info(f"Starting agent with prompt: {prompt}")

    if conversation_id:
        update_conversation_status(conversation_id, "planning")
        add_conversation_message(conversation_id, "system", "Planning execution...")
    notify("status", {"type": "planning", "message": "Planning the implementation..."})

    plan = run_planner(prompt)

    if plan["type"] == "clarification":
        questions = plan.get("questions", [])
        if conversation_id:
            update_conversation_status(conversation_id, "clarification_needed")
            add_conversation_message(conversation_id, "system", f"Asking for clarification: {questions}")
        notify("clarification", {"questions": questions, "conversation_id": conversation_id})
        return {
            "success": False,
            "needs_clarification": True,
            "questions": questions,
            "conversation_id": conversation_id
        }

    todos = plan.get("todos", [])
    brief = plan.get("brief", prompt)
    if conversation_id:
        update_todos(conversation_id, todos)
        add_conversation_message(conversation_id, "system", f"Plan: {brief}")
    notify("todos", {"todos": todos, "brief": brief})

    project_id = project_manager.create_project()
    project_path = project_manager.active_project_path

    if conversation_id:
        update_conversation_status(conversation_id, "executing", {"project_id": project_id})
        add_conversation_message(conversation_id, "system", f"Created project {project_id}")
    notify("status", {"type": "project_created", "message": f"Created project {project_id}"})

    print(f"\n{'='*60}\nStarting new project: project_{project_id}\nWorkspace: {project_path}\n{'='*60}\n")

    try:
        notify("status", {"type": "scaffolding", "message": "Scaffolding project..."})
        scaffold_result = scaffold_project()
        if not scaffold_result.get("success", True):
            notify("error", {"error": f"Scaffold failed: {scaffold_result.get('output')}"})
            return {"success": False, "message": "Scaffold failed", "project_id": project_id}

        notify("status", {"type": "generating", "message": "Generating app code..."})
        files = _run_with_retry(lambda: run_codegen(brief, todos), notify, "codegen")
        write_generated_files(files)
        notify("status", {"type": "generated", "message": f"Wrote {len(files)} files"})

        notify("status", {"type": "building", "message": "Running build check..."})
        build_result = check_build()

        message = f"Built {brief} successfully."
        if not build_result.get("success", True):
            notify("status", {"type": "fixing", "message": "Build failed, attempting fixes..."})
            fixer_instruction = (
                "The generated app fails to build. Fix it.\n\n"
                f"Build output:\n{build_result.get('output', '')}"
            )
            message = _run_with_retry(
                lambda: run_fixer(fixer_instruction, notify, conversation_id=conversation_id),
                notify,
                "fixer",
            )

    except UsageLimitExceeded:
        notify("error", {"error": "Fixer exceeded max iterations"})
        return {"success": False, "message": "Fixer exceeded max iterations", "project_id": project_id}
    except (ModelAPIError, ModelHTTPError) as e:
        if _is_daily_quota_error(e):
            notify("error", {"error": "Daily token quota exhausted - try again after the quota resets, or upgrade tier."})
            return {"success": False, "message": "Daily token quota exhausted", "project_id": project_id}
        logger.error(f"API Error: {e}", exc_info=True)
        notify("error", {"error": f"API Error: {str(e)}"})
        return {"success": False, "message": f"API Error: {str(e)}", "project_id": project_id}
    except Exception as e:
        logger.error(f"API Error: {e}", exc_info=True)
        notify("error", {"error": f"API Error: {str(e)}"})
        return {"success": False, "message": f"API Error: {str(e)}", "project_id": project_id}

    if conversation_id:
        add_conversation_message(conversation_id, "assistant", message)
        update_conversation_status(conversation_id, "complete")

    return {
        "success": True,
        "message": message,
        "project_id": project_id,
        "project_path": str(project_path)
    }