#!/usr/bin/env python3
"""
ForgeExec v1 — Guarded Executor (Single-File Implementation)

Blueprints: FORGEEXEC v1 — FROZEN SPEC (approved)
- Minimal, auditable executor for safe changes inside Val0 repo
- Reads tasks JSON v1, reads files from disk (no guessing), calls OpenAI API,
  writes ONLY inside repo_root with dual-guard safety checks, creates backups,
  runs allowlisted tests, logs everything as JSONL with timestamps.

This file is the single "main entrypoint" implementation. It contains the v1
modules (loader, validator, prompt builder, OpenAI client, file ops, tests,
logging, models) inline to keep dependencies minimal.

Run:
  python3 tools/forgeexec/forgeexec.py --config tools/forgeexec/config/config.json --tasks tools/forgeexec/tasks/tasks.json

Safe defaults:
- dry_run_default = true (config)
- allow_delete = false (config)
- stop_on_fail = true (config)

Minimal dependencies:
- Python stdlib only
- OpenAI API calls via urllib (HTTPS). Network restricted to OpenAI API only (by policy).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib import request as urlrequest
from urllib.error import URLError, HTTPError


# =========================
# Models (v1)
# =========================

JSONValue = Union[dict, list, str, int, float, bool, None]


@dataclass(frozen=True)
class OpenAIConfig:
    api_key_env: str
    model: str
    timeout_s: int = 60
    max_retries: int = 2


@dataclass(frozen=True)
class LoggingConfig:
    log_dir: str
    level: str = "info"


@dataclass(frozen=True)
class ExecutionConfig:
    dry_run_default: bool = True
    stop_on_fail: bool = True


@dataclass(frozen=True)
class ForgeConfig:
    repo_root: str
    allowed_write_paths: List[str]  # repo-relative prefixes
    allowed_file_extensions: List[str]  # extensions including dot e.g. [".py", ".md", ".json"]
    allow_delete: bool = False
    openai: OpenAIConfig = OpenAIConfig(api_key_env="OPENAI_API_KEY", model="gpt-4.1-mini")
    tests_allowlist: Dict[str, str] = None  # test_id -> command string
    logging: LoggingConfig = LoggingConfig(log_dir="tools/forgeexec/logs")
    execution: ExecutionConfig = ExecutionConfig()


@dataclass(frozen=True)
class ModifyFileAction:
    path: str  # repo-relative
    operation: str  # create | update | delete
    backup: bool = True


@dataclass(frozen=True)
class TaskInputs:
    read_files: List[str]
    constraints: Optional[str] = None


@dataclass(frozen=True)
class TaskActions:
    modify_files: List[ModifyFileAction]
    run_tests: List[str]


@dataclass(frozen=True)
class TaskSpec:
    id: str
    title: str
    goal: str
    context: Union[str, List[str]]
    inputs: TaskInputs
    actions: TaskActions
    acceptance: List[str]
    risk_level: str  # low | medium | high
    dry_run: Optional[bool] = None
    enabled: bool = True


@dataclass(frozen=True)
class TasksFile:
    version: str
    repo_root: str
    tasks: List[TaskSpec]


# =========================
# Logger (JSONL)
# =========================

class JSONLLogger:
    def __init__(self, log_dir: str, run_id: str):
        self.run_id = run_id
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        date_str = _dt.datetime.now().strftime("%Y%m%d")
        self.log_path = os.path.join(self.log_dir, f"forgeexec_{date_str}.jsonl")

    @staticmethod
    def _iso_ts() -> str:
        return _dt.datetime.now(tz=_dt.timezone.utc).astimezone().isoformat()

    def log(
        self,
        task_id: str,
        step: str,
        status: str,
        details: Dict[str, Any],
        duration_ms: Optional[int] = None,
    ) -> None:
        entry: Dict[str, Any] = {
            "ts": self._iso_ts(),
            "run_id": self.run_id,
            "task_id": task_id,
            "step": step,
            "status": status,
            "details": details,
        }
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# =========================
# Utility / Safety
# =========================

class ForgeExecError(Exception):
    pass


def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_bytes_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def write_bytes_file(path: str, content: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)


def normalize_repo_rel_path(p: str) -> str:
    """Normalize to posix-ish internal form. Reject absolute and traversal."""
    if p is None:
        raise ForgeExecError("Path is missing.")
    if os.path.isabs(p):
        raise ForgeExecError(f"Absolute path rejected: {p}")
    # Reject traversal tokens explicitly (Blueprint rule)
    parts = p.replace("\\", "/").split("/")
    if any(part == ".." for part in parts):
        raise ForgeExecError(f"Path traversal rejected: {p}")
    # Normalize redundant separators/dots
    norm = os.path.normpath(p).replace("\\", "/")
    if norm.startswith("../") or norm == "..":
        raise ForgeExecError(f"Path traversal rejected after normalization: {p}")
    if norm.startswith("/"):
        raise ForgeExecError(f"Absolute path rejected after normalization: {p}")
    return norm


def realpath_inside_repo(repo_root: str, repo_rel: str) -> str:
    """
    Dual-guard filesystem check:
    1) Build joined path and realpath it (resolves symlinks).
    2) Ensure it stays within repo_root realpath.
    """
    repo_root_real = os.path.realpath(repo_root)
    target_joined = os.path.join(repo_root_real, repo_rel)
    target_real = os.path.realpath(target_joined)

    # Ensure repo_root ends with separator to avoid prefix tricks: /opt/val0X
    repo_prefix = repo_root_real if repo_root_real.endswith(os.sep) else repo_root_real + os.sep
    if not (target_real == repo_root_real or target_real.startswith(repo_prefix)):
        raise ForgeExecError(f"Symlink/path escape blocked: {repo_rel} -> {target_real}")
    return target_real


def is_allowed_write_path(repo_rel: str, allowed_prefixes: List[str]) -> bool:
    # Allowed prefixes are repo-relative; treat as directory or exact prefix
    rr = repo_rel.replace("\\", "/")
    for pref in allowed_prefixes:
        p = normalize_repo_rel_path(pref)
        if p == ".":
            return True
        p = p.rstrip("/")
        if rr == p or rr.startswith(p + "/"):
            return True
    return False


def extension_allowed(repo_rel: str, allowed_exts: List[str]) -> bool:
    _, ext = os.path.splitext(repo_rel)
    return ext in set(allowed_exts)


# =========================
# Config loader
# =========================

def load_config(config_path: str) -> ForgeConfig:
    if not os.path.exists(config_path):
        raise ForgeExecError(f"Config file missing: {config_path}")

    raw = json.loads(read_text_file(config_path))

    def req(field: str) -> Any:
        if field not in raw:
            raise ForgeExecError(f"Config missing required field: {field}")
        return raw[field]

    repo_root = req("repo_root")
    allowed_write_paths = req("allowed_write_paths")
    allowed_file_extensions = req("allowed_file_extensions")
    allow_delete = bool(raw.get("allow_delete", False))

    openai_raw = req("openai")
    openai_cfg = OpenAIConfig(
        api_key_env=str(openai_raw.get("api_key_env", "OPENAI_API_KEY")),
        model=str(openai_raw.get("model", "gpt-4.1-mini")),
        timeout_s=int(openai_raw.get("timeout_s", 60)),
        max_retries=int(openai_raw.get("max_retries", 2)),
    )

    tests_allowlist = raw.get("tests_allowlist", {})
    if not isinstance(tests_allowlist, dict):
        raise ForgeExecError("Config tests_allowlist must be an object mapping test_id -> command")

    logging_raw = req("logging")
    logging_cfg = LoggingConfig(
        log_dir=str(logging_raw.get("log_dir", "tools/forgeexec/logs")),
        level=str(logging_raw.get("level", "info")),
    )

    exec_raw = req("execution")
    exec_cfg = ExecutionConfig(
        dry_run_default=bool(exec_raw.get("dry_run_default", True)),
        stop_on_fail=bool(exec_raw.get("stop_on_fail", True)),
    )

    return ForgeConfig(
        repo_root=str(repo_root),
        allowed_write_paths=list(allowed_write_paths),
        allowed_file_extensions=list(allowed_file_extensions),
        allow_delete=allow_delete,
        openai=openai_cfg,
        tests_allowlist=dict(tests_allowlist),
        logging=logging_cfg,
        execution=exec_cfg,
    )


# =========================
# Task loader + validator (JSON v1)
# =========================

def load_tasks_file(tasks_path: str) -> TasksFile:
    if not os.path.exists(tasks_path):
        raise ForgeExecError(f"Tasks file missing: {tasks_path}")

    raw = json.loads(read_text_file(tasks_path))

    version = raw.get("version")
    repo_root = raw.get("repo_root")
    tasks_raw = raw.get("tasks")

    if version != "1.0":
        raise ForgeExecError(f"Unsupported tasks version: {version} (expected '1.0')")
    if not isinstance(repo_root, str) or not repo_root:
        raise ForgeExecError("tasks.json repo_root must be a non-empty string")
    if not isinstance(tasks_raw, list):
        raise ForgeExecError("tasks.json tasks must be a list")

    tasks: List[TaskSpec] = []
    seen_ids = set()

    for t in tasks_raw:
        if not isinstance(t, dict):
            raise ForgeExecError("Task entry must be an object")
        tid = str(t.get("id", "")).strip()
        if not tid:
            raise ForgeExecError("Task missing id")
        if tid in seen_ids:
            raise ForgeExecError(f"Duplicate task id: {tid}")
        seen_ids.add(tid)

        title = str(t.get("title", "")).strip()
        goal = str(t.get("goal", "")).strip()
        if not title or not goal:
            raise ForgeExecError(f"Task {tid} missing title/goal")

        context = t.get("context", "")
        if not isinstance(context, (str, list)):
            raise ForgeExecError(f"Task {tid} context must be string or array of strings")
        if isinstance(context, list) and not all(isinstance(x, str) for x in context):
            raise ForgeExecError(f"Task {tid} context array must be strings only")

        inputs_raw = t.get("inputs", {})
        if not isinstance(inputs_raw, dict):
            raise ForgeExecError(f"Task {tid} inputs must be an object")
        read_files = inputs_raw.get("read_files", [])
        if not isinstance(read_files, list) or not all(isinstance(x, str) for x in read_files):
            raise ForgeExecError(f"Task {tid} inputs.read_files must be a list of strings")
        constraints = inputs_raw.get("constraints")
        if constraints is not None and not isinstance(constraints, str):
            raise ForgeExecError(f"Task {tid} inputs.constraints must be string if provided")

        actions_raw = t.get("actions", {})
        if not isinstance(actions_raw, dict):
            raise ForgeExecError(f"Task {tid} actions must be an object")

        mf_raw = actions_raw.get("modify_files", [])
        if not isinstance(mf_raw, list):
            raise ForgeExecError(f"Task {tid} actions.modify_files must be a list")
        modify_files: List[ModifyFileAction] = []
        for mf in mf_raw:
            if not isinstance(mf, dict):
                raise ForgeExecError(f"Task {tid} modify_files entry must be an object")
            path = str(mf.get("path", "")).strip()
            operation = str(mf.get("operation", "")).strip()
            if operation not in ("create", "update", "delete"):
                raise ForgeExecError(f"Task {tid} invalid operation: {operation}")
            backup = bool(mf.get("backup", True))
            modify_files.append(ModifyFileAction(path=path, operation=operation, backup=backup))

        run_tests_raw = actions_raw.get("run_tests", [])
        if not isinstance(run_tests_raw, list) or not all(isinstance(x, str) for x in run_tests_raw):
            raise ForgeExecError(f"Task {tid} actions.run_tests must be a list of strings")
        actions = TaskActions(modify_files=modify_files, run_tests=run_tests_raw)

        acceptance = t.get("acceptance", [])
        if not isinstance(acceptance, list) or not all(isinstance(x, str) for x in acceptance):
            raise ForgeExecError(f"Task {tid} acceptance must be a list of strings")

        risk_level = str(t.get("risk_level", "low")).strip()
        if risk_level not in ("low", "medium", "high"):
            raise ForgeExecError(f"Task {tid} risk_level must be low|medium|high")

        dry_run_val = t.get("dry_run")
        if dry_run_val is not None and not isinstance(dry_run_val, bool):
            raise ForgeExecError(f"Task {tid} dry_run must be boolean if provided")

        enabled = bool(t.get("enabled", True))

        tasks.append(TaskSpec(
            id=tid,
            title=title,
            goal=goal,
            context=context,
            inputs=TaskInputs(read_files=read_files, constraints=constraints),
            actions=actions,
            acceptance=acceptance,
            risk_level=risk_level,
            dry_run=dry_run_val,
            enabled=enabled,
        ))

    return TasksFile(version=version, repo_root=repo_root, tasks=tasks)


def validate_tasks_against_config(cfg: ForgeConfig, tf: TasksFile) -> List[TaskSpec]:
    # Repo root match required (Blueprint rule)
    if os.path.realpath(tf.repo_root) != os.path.realpath(cfg.repo_root):
        raise ForgeExecError(f"repo_root mismatch: tasks={tf.repo_root} config={cfg.repo_root}")

    valid: List[TaskSpec] = []

    for t in tf.tasks:
        if not t.enabled:
            continue

        # Validate read_files paths are safe and inside repo
        for rf in t.inputs.read_files:
            rr = normalize_repo_rel_path(rf)
            _ = realpath_inside_repo(cfg.repo_root, rr)  # will raise if escape

        # Validate modify_files paths are safe, allowed, and extension allowed (for create/update)
        for mf in t.actions.modify_files:
            rr = normalize_repo_rel_path(mf.path)
            _ = realpath_inside_repo(cfg.repo_root, rr)  # will raise if escape

            if mf.operation == "delete" and not cfg.allow_delete:
                raise ForgeExecError(f"Task {t.id} requests delete but allow_delete is false (path={mf.path})")

            if mf.operation in ("create", "update"):
                if not is_allowed_write_path(rr, cfg.allowed_write_paths):
                    raise ForgeExecError(f"Task {t.id} write path not allowed: {mf.path}")
                if not extension_allowed(rr, cfg.allowed_file_extensions):
                    raise ForgeExecError(f"Task {t.id} file extension not allowed: {mf.path}")

        # Validate allowlisted tests
        for test_id in t.actions.run_tests:
            if test_id not in cfg.tests_allowlist:
                raise ForgeExecError(f"Task {t.id} references non-allowlisted test_id: {test_id}")

        valid.append(t)

    return valid


# =========================
# Prompt builder
# =========================

def build_prompt_for_task(cfg: ForgeConfig, task: TaskSpec, files_context: Dict[str, str]) -> str:
    """
    Build explicit prompt:
    - policy
    - goal/context
    - constraints
    - full file contents for all read_files
    - explicit requirement: return structured JSON with full file contents (no patches)
    """
    policy = f"""
You are ForgeExec v1, a guarded code executor.

NON-NEGOTIABLE RULES:
- You MUST NOT guess file contents. If required info is missing, declare unknowns.
- You MUST output full file contents for any file you propose to create or update. NO patches.
- You MUST only propose file changes exactly for the requested actions.modify_files list.
- All paths are repo-relative.
- If you cannot comply, return unknowns and an empty changes list.

OUTPUT FORMAT (strict JSON):
{{
  "unknowns": [ "...", ... ],
  "changes": [
    {{
      "path": "repo/relative/path.ext",
      "operation": "create|update|delete",
      "content": "FULL FILE CONTENTS HERE (required for create/update; omit or null for delete)"
    }},
    ...
  ]
}}

IMPORTANT:
- "changes" MUST match the requested modify_files list (same paths + operations).
- For delete: content must be null.
- For create/update: content must be a string with full file content.

Task risk level: {task.risk_level}
""".strip()

    context_block = task.context if isinstance(task.context, str) else "\n".join(task.context)
    constraints = task.inputs.constraints or "(none)"

    # Include file contents (must be read from disk or fail before prompt)
    files_blob_lines = []
    for path, content in files_context.items():
        files_blob_lines.append(f"===== FILE: {path} =====\n{content}\n===== END FILE: {path} =====\n")

    files_blob = "\n".join(files_blob_lines).strip() if files_blob_lines else "(no files provided)"

    requested_actions_lines = []
    for mf in task.actions.modify_files:
        requested_actions_lines.append(f"- {mf.operation.upper()} {normalize_repo_rel_path(mf.path)} (backup={mf.backup})")
    requested_actions = "\n".join(requested_actions_lines) if requested_actions_lines else "(no file modifications requested)"

    prompt = f"""
{policy}

TASK:
- id: {task.id}
- title: {task.title}
- goal: {task.goal}

CONTEXT:
{context_block}

CONSTRAINTS:
{constraints}

REQUESTED FILE ACTIONS:
{requested_actions}

FILE CONTENTS (read from disk):
{files_blob}
""".strip()

    return prompt


# =========================
# OpenAI client (stdlib HTTPS)
# =========================

class OpenAIClient:
    """
    Minimal OpenAI Chat Completions client via HTTPS.
    Network usage is limited to OpenAI API endpoint.
    """

    def __init__(self, api_key: str, model: str, timeout_s: int, max_retries: int):
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s
        self.max_retries = max_retries

    def chat_json(self, prompt: str) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Return ONLY valid JSON. No markdown. No commentary."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
        }

        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                req = urlrequest.Request(url, data=body, headers=headers, method="POST")
                with urlrequest.urlopen(req, timeout=self.timeout_s) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                data = json.loads(raw)

                # Extract assistant content
                choices = data.get("choices", [])
                if not choices:
                    raise ForgeExecError("OpenAI response missing choices")
                content = choices[0]["message"]["content"]
                # Must be strict JSON
                return json.loads(content)
            except (HTTPError, URLError, json.JSONDecodeError, KeyError, ForgeExecError) as e:
                last_err = e
                # conservative backoff
                time.sleep(min(2 ** attempt, 8))
                continue

        raise ForgeExecError(f"OpenAI API call failed after retries: {last_err}")


# =========================
# File operations + backups
# =========================

def ensure_tool_dirs_exist(cfg: ForgeConfig) -> None:
    # Ensure logging dir and backups dir exist relative to repo_root
    log_dir_abs = realpath_inside_repo(cfg.repo_root, normalize_repo_rel_path(cfg.logging.log_dir))
    backups_rel = "tools/forgeexec/backups"
    backups_abs = realpath_inside_repo(cfg.repo_root, backups_rel)
    os.makedirs(log_dir_abs, exist_ok=True)
    os.makedirs(backups_abs, exist_ok=True)


def backup_file(cfg: ForgeConfig, run_id: str, task_id: str, repo_rel_path: str, logger: JSONLLogger) -> Tuple[str, Dict[str, Any]]:
    """
    Backup ALWAYS before write (except create), per spec.
    Backup includes original file bytes + metadata.json.
    """
    repo_rel_path = normalize_repo_rel_path(repo_rel_path)
    src_abs = realpath_inside_repo(cfg.repo_root, repo_rel_path)

    if not os.path.exists(src_abs):
        raise ForgeExecError(f"Cannot backup missing file: {repo_rel_path}")

    b_root_rel = f"tools/forgeexec/backups/{run_id}/{task_id}"
    b_root_abs = realpath_inside_repo(cfg.repo_root, b_root_rel)
    os.makedirs(b_root_abs, exist_ok=True)

    original_bytes = read_bytes_file(src_abs)
    pre_sha = sha256_bytes(original_bytes)
    size = len(original_bytes)

    # Preserve file basename
    backup_file_path = os.path.join(b_root_abs, os.path.basename(repo_rel_path))
    write_bytes_file(backup_file_path, original_bytes)

    meta = {
        "timestamp": _dt.datetime.now(tz=_dt.timezone.utc).astimezone().isoformat(),
        "repo_rel_path": repo_rel_path,
        "sha256": pre_sha,
        "size": size,
    }
    meta_path = os.path.join(b_root_abs, "metadata.json")
    write_bytes_file(meta_path, json.dumps(meta, indent=2).encode("utf-8"))

    logger.log(
        task_id=task_id,
        step="backup",
        status="ok",
        details={
            "backup_path": os.path.relpath(backup_file_path, start=realpath_inside_repo(cfg.repo_root, ".")),
            "file_path": repo_rel_path,
            "byte_size": size,
            "sha256": pre_sha,
            "metadata_path": os.path.relpath(meta_path, start=realpath_inside_repo(cfg.repo_root, ".")),
        },
    )

    return backup_file_path, meta


def write_file_with_audit(
    cfg: ForgeConfig,
    task_id: str,
    repo_rel_path: str,
    content_text: str,
    logger: JSONLLogger,
    backup_path: Optional[str],
) -> None:
    repo_rel_path = normalize_repo_rel_path(repo_rel_path)
    dst_abs = realpath_inside_repo(cfg.repo_root, repo_rel_path)

    # compute pre-state
    pre_bytes: Optional[bytes] = None
    pre_sha: Optional[str] = None
    pre_size: Optional[int] = None
    if os.path.exists(dst_abs):
        pre_bytes = read_bytes_file(dst_abs)
        pre_sha = sha256_bytes(pre_bytes)
        pre_size = len(pre_bytes)

    new_bytes = content_text.encode("utf-8")
    post_sha = sha256_bytes(new_bytes)
    post_size = len(new_bytes)

    # write
    os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
    with open(dst_abs, "wb") as f:
        f.write(new_bytes)

    logger.log(
        task_id=task_id,
        step="write",
        status="ok",
        details={
            "backup_path": backup_path,
            "file_path": repo_rel_path,
            "byte_size": post_size,
            "pre_sha256": pre_sha,
            "post_sha256": post_sha,
            "pre_size": pre_size,
            "post_size": post_size,
        },
    )


def delete_file_with_audit(
    cfg: ForgeConfig,
    task_id: str,
    repo_rel_path: str,
    logger: JSONLLogger,
    backup_path: Optional[str],
) -> None:
    repo_rel_path = normalize_repo_rel_path(repo_rel_path)
    dst_abs = realpath_inside_repo(cfg.repo_root, repo_rel_path)

    if os.path.exists(dst_abs):
        pre_bytes = read_bytes_file(dst_abs)
        pre_sha = sha256_bytes(pre_bytes)
        pre_size = len(pre_bytes)
    else:
        pre_sha = None
        pre_size = None

    if os.path.isdir(dst_abs):
        raise ForgeExecError(f"Refusing to delete directory: {repo_rel_path}")

    if os.path.exists(dst_abs):
        os.remove(dst_abs)

    logger.log(
        task_id=task_id,
        step="delete",
        status="ok",
        details={
            "backup_path": backup_path,
            "file_path": repo_rel_path,
            "pre_sha256": pre_sha,
            "pre_size": pre_size,
        },
    )


# =========================
# Test runner (allowlist only)
# =========================

def run_allowlisted_tests(cfg: ForgeConfig, task_id: str, test_ids: List[str], logger: JSONLLogger) -> bool:
    if not test_ids:
        logger.log(task_id=task_id, step="tests", status="skip", details={"reason": "no tests requested"})
        return True

    all_ok = True
    for test_id in test_ids:
        cmd_str = cfg.tests_allowlist.get(test_id)
        if cmd_str is None:
            raise ForgeExecError(f"Non-allowlisted test_id: {test_id}")

        # No arbitrary shell execution. Use shlex split, shell=False.
        args = shlex.split(cmd_str)
        start = time.time()
        try:
            proc = subprocess.run(
                args,
                cwd=cfg.repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                check=False,
            )
            dur_ms = int((time.time() - start) * 1000)
            ok = (proc.returncode == 0)
            all_ok = all_ok and ok
            logger.log(
                task_id=task_id,
                step="test",
                status="ok" if ok else "fail",
                details={
                    "test_id": test_id,
                    "command": cmd_str,
                    "returncode": proc.returncode,
                    "stdout": proc.stdout[-4000:],  # cap to keep logs reasonable
                    "stderr": proc.stderr[-4000:],
                },
                duration_ms=dur_ms,
            )
        except Exception as e:
            dur_ms = int((time.time() - start) * 1000)
            all_ok = False
            logger.log(
                task_id=task_id,
                step="test",
                status="fail",
                details={"test_id": test_id, "command": cmd_str, "error": str(e)},
                duration_ms=dur_ms,
            )

    return all_ok


# =========================
# Structured OpenAI output validation
# =========================

def validate_openai_output(task: TaskSpec, out: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]]]:
    if not isinstance(out, dict):
        raise ForgeExecError("OpenAI output must be a JSON object")
    unknowns = out.get("unknowns", [])
    changes = out.get("changes", [])

    if not isinstance(unknowns, list) or not all(isinstance(x, str) for x in unknowns):
        raise ForgeExecError("OpenAI output unknowns must be a list of strings")
    if not isinstance(changes, list) or not all(isinstance(x, dict) for x in changes):
        raise ForgeExecError("OpenAI output changes must be a list of objects")

    # Must match requested modify_files exactly (paths + operations)
    requested = [(normalize_repo_rel_path(mf.path), mf.operation) for mf in task.actions.modify_files]
    got = []
    for ch in changes:
        path = ch.get("path")
        op = ch.get("operation")
        if not isinstance(path, str) or not isinstance(op, str):
            raise ForgeExecError("Each change must include string fields: path, operation")
        rr = normalize_repo_rel_path(path)
        if op not in ("create", "update", "delete"):
            raise ForgeExecError(f"Invalid operation in OpenAI output: {op}")
        got.append((rr, op))

        content = ch.get("content", None)
        if op in ("create", "update"):
            if not isinstance(content, str):
                raise ForgeExecError(f"Change {rr} ({op}) must include full string content")
        elif op == "delete":
            if content is not None:
                raise ForgeExecError(f"Change {rr} (delete) content must be null")

    if requested != got:
        raise ForgeExecError(
            "OpenAI output changes do not match requested modify_files list exactly. "
            f"requested={requested} got={got}"
        )

    return unknowns, changes


# =========================
# Executor
# =========================

def read_required_files(cfg: ForgeConfig, task: TaskSpec) -> Dict[str, str]:
    files_context: Dict[str, str] = {}
    for rf in task.inputs.read_files:
        rr = normalize_repo_rel_path(rf)
        abs_path = realpath_inside_repo(cfg.repo_root, rr)
        if not os.path.exists(abs_path):
            raise ForgeExecError(f"Required read file missing: {rr}")
        files_context[rr] = read_text_file(abs_path)
    return files_context


def apply_task_changes(
    cfg: ForgeConfig,
    run_id: str,
    task: TaskSpec,
    changes: List[Dict[str, Any]],
    logger: JSONLLogger,
    dry_run: bool,
) -> bool:
    """
    Apply changes in order. Backups before writes (except create), per spec.
    No auto-rollback in v1.
    Returns True if applied successfully (or dry-run planned successfully).
    """
    # If dry_run: log planned changes only
    if dry_run:
        planned = []
        for ch in changes:
            planned.append({
                "path": ch["path"],
                "operation": ch["operation"],
                "content_bytes": len(ch["content"].encode("utf-8")) if ch["operation"] in ("create", "update") else None,
            })
        logger.log(task_id=task.id, step="dry_run", status="ok", details={"planned_changes": planned})
        return True

    # Non-dry-run: write/delete with backups + audit logs
    for ch in changes:
        rr = normalize_repo_rel_path(ch["path"])
        op = ch["operation"]

        # Dual-guard: ensure inside repo and allowed
        _ = realpath_inside_repo(cfg.repo_root, rr)
        if op in ("create", "update"):
            if not is_allowed_write_path(rr, cfg.allowed_write_paths):
                raise ForgeExecError(f"Write path not allowed by config: {rr}")
            if not extension_allowed(rr, cfg.allowed_file_extensions):
                raise ForgeExecError(f"File extension not allowed by config: {rr}")
        if op == "delete" and not cfg.allow_delete:
            raise ForgeExecError(f"Delete not allowed by config: {rr}")

        backup_path: Optional[str] = None
        # Backup ALWAYS before write (except create). Also backup before delete (recommended for audit).
        # Spec explicitly requires before write; for delete, we also backup if the file exists and backup is true in task spec.
        matching_action = next((mf for mf in task.actions.modify_files if normalize_repo_rel_path(mf.path) == rr and mf.operation == op), None)
        do_backup = True if matching_action is None else bool(matching_action.backup)

        if op == "update":
            if do_backup:
                backup_abs, _ = backup_file(cfg, run_id, task.id, rr, logger)
                backup_path = os.path.relpath(backup_abs, start=realpath_inside_repo(cfg.repo_root, "."))
            write_file_with_audit(cfg, task.id, rr, ch["content"], logger, backup_path)

        elif op == "create":
            # no backup for create per spec
            write_file_with_audit(cfg, task.id, rr, ch["content"], logger, backup_path=None)

        elif op == "delete":
            if do_backup:
                # backup before delete if file exists (auditable)
                abs_path = realpath_inside_repo(cfg.repo_root, rr)
                if os.path.exists(abs_path):
                    backup_abs, _ = backup_file(cfg, run_id, task.id, rr, logger)
                    backup_path = os.path.relpath(backup_abs, start=realpath_inside_repo(cfg.repo_root, "."))
            delete_file_with_audit(cfg, task.id, rr, logger, backup_path)

    return True


def execute_tasks(cfg: ForgeConfig, tasks_file: TasksFile, tasks: List[TaskSpec], logger: JSONLLogger) -> int:
    ensure_tool_dirs_exist(cfg)

    # OpenAI client init (only dependency is env var)
    api_key = os.environ.get(cfg.openai.api_key_env)
    if not api_key:
        raise ForgeExecError(f"OpenAI API key env missing: {cfg.openai.api_key_env}")

    client = OpenAIClient(
        api_key=api_key,
        model=cfg.openai.model,
        timeout_s=cfg.openai.timeout_s,
        max_retries=cfg.openai.max_retries,
    )

    failures = 0

    for task in tasks:
        start_task = time.time()
        # Determine dry run mode
        dry_run = task.dry_run if task.dry_run is not None else cfg.execution.dry_run_default

        logger.log(task_id=task.id, step="task_start", status="ok", details={
            "title": task.title,
            "goal": task.goal,
            "risk_level": task.risk_level,
            "dry_run": dry_run,
            "acceptance": task.acceptance,
        })

        try:
            # Read required files
            t0 = time.time()
            files_context = read_required_files(cfg, task)
            logger.log(task_id=task.id, step="read_files", status="ok", details={
                "files": list(files_context.keys()),
            }, duration_ms=int((time.time() - t0) * 1000))

            # Build prompt
            t1 = time.time()
            prompt = build_prompt_for_task(cfg, task, files_context)
            logger.log(task_id=task.id, step="prompt_built", status="ok", details={
                "prompt_chars": len(prompt),
                "read_files_count": len(files_context),
                "modify_files_count": len(task.actions.modify_files),
                "tests_count": len(task.actions.run_tests),
            }, duration_ms=int((time.time() - t1) * 1000))

            # Call OpenAI
            t2 = time.time()
            out = client.chat_json(prompt)
            logger.log(task_id=task.id, step="openai_response", status="ok", details={
                "raw_keys": list(out.keys()) if isinstance(out, dict) else None,
            }, duration_ms=int((time.time() - t2) * 1000))

            # Validate OpenAI output
            t3 = time.time()
            unknowns, changes = validate_openai_output(task, out)
            logger.log(task_id=task.id, step="openai_output_validated", status="ok", details={
                "unknowns": unknowns,
                "changes_count": len(changes),
            }, duration_ms=int((time.time() - t3) * 1000))

            # If unknowns exist, we do not apply changes (guarded execution)
            if unknowns:
                logger.log(task_id=task.id, step="unknowns_present", status="fail", details={
                    "unknowns": unknowns,
                    "note": "Task requires missing information; no changes applied.",
                })
                failures += 1
                if cfg.execution.stop_on_fail:
                    break
                continue

            # Apply (or plan) changes
            t4 = time.time()
            ok_apply = apply_task_changes(cfg, logger.run_id, task, changes, logger, dry_run)
            logger.log(task_id=task.id, step="apply_changes", status="ok" if ok_apply else "fail", details={
                "dry_run": dry_run,
            }, duration_ms=int((time.time() - t4) * 1000))

            # Run allowlisted tests (only if not dry-run)
            if not dry_run:
                ok_tests = run_allowlisted_tests(cfg, task.id, task.actions.run_tests, logger)
                if not ok_tests:
                    failures += 1
                    if cfg.execution.stop_on_fail:
                        break

            logger.log(task_id=task.id, step="task_done", status="ok", details={
                "dry_run": dry_run,
                "duration_ms": int((time.time() - start_task) * 1000),
            })

        except ForgeExecError as e:
            failures += 1
            logger.log(task_id=task.id, step="task_error", status="fail", details={
                "error": str(e),
                "manual_rollback": (
                    "No auto-rollback in v1. Use backups under "
                    f"tools/forgeexec/backups/{logger.run_id}/{task.id}/"
                    " to restore files if needed."
                ),
            }, duration_ms=int((time.time() - start_task) * 1000))
            if cfg.execution.stop_on_fail:
                break
        except Exception as e:
            failures += 1
            logger.log(task_id=task.id, step="task_error", status="fail", details={
                "error": f"Unhandled error: {type(e).__name__}: {e}",
                "manual_rollback": (
                    "No auto-rollback in v1. Use backups under "
                    f"tools/forgeexec/backups/{logger.run_id}/{task.id}/"
                ),
            }, duration_ms=int((time.time() - start_task) * 1000))
            if cfg.execution.stop_on_fail:
                break

    return failures


# =========================
# CLI
# =========================

def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ForgeExec v1 — Guarded executor for Val0 repo changes")
    p.add_argument("--config", required=True, help="Path to config.json (repo-relative or absolute)")
    p.add_argument("--tasks", required=True, help="Path to tasks.json (repo-relative or absolute)")
    return p.parse_args(argv)


def resolve_path_maybe_repo_relative(repo_root: str, p: str) -> str:
    # For config/tasks file path, we allow absolute or repo-relative for convenience;
    # safety constraints apply to file modifications, not these inputs.
    if os.path.isabs(p):
        return p
    return os.path.join(repo_root, p)


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    # Load config first (requires file)
    # If config path is repo-relative, assume current working directory is anywhere; resolve from CWD.
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.abspath(config_path)

    cfg = load_config(config_path)

    run_id = str(uuid.uuid4())
    logger = JSONLLogger(
        log_dir=realpath_inside_repo(cfg.repo_root, normalize_repo_rel_path(cfg.logging.log_dir)),
        run_id=run_id,
    )

    # Resolve tasks path (may be repo-relative to repo_root, but allow absolute)
    tasks_path = args.tasks
    if not os.path.isabs(tasks_path):
        tasks_path = os.path.join(cfg.repo_root, tasks_path)

    # Start run log
    logger.log(task_id="(run)", step="run_start", status="ok", details={
        "repo_root": cfg.repo_root,
        "config_path": os.path.abspath(config_path),
        "tasks_path": os.path.abspath(tasks_path),
        "model": cfg.openai.model,
        "dry_run_default": cfg.execution.dry_run_default,
        "stop_on_fail": cfg.execution.stop_on_fail,
        "allow_delete": cfg.allow_delete,
    })

    try:
        tasks_file = load_tasks_file(tasks_path)
        tasks = validate_tasks_against_config(cfg, tasks_file)
    except ForgeExecError as e:
        logger.log(task_id="(run)", step="init_error", status="fail", details={"error": str(e)})
        return 2

    # Execute
    failures = execute_tasks(cfg, tasks_file, tasks, logger)
    status = "ok" if failures == 0 else "fail"
    logger.log(task_id="(run)", step="run_done", status=status, details={"failures": failures})

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
