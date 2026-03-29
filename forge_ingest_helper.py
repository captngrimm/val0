#!/usr/bin/env python3

import os
import json
import subprocess
from datetime import datetime

FORGE_HOST = "forge@100.88.212.83"
REMOTE_TRIGGER = "python3 /opt/valprime/trigger_ingest.py"
REMOTE_TMP_DIR = "/tmp"
LOCAL_RESPONSE_DIR = "/opt/val0/forge_responses"
LOCAL_LOG_PATH = "/opt/val0/forge_ingest_log.jsonl"


def ensure_dirs():
    os.makedirs(LOCAL_RESPONSE_DIR, exist_ok=True)


def save_response_packet(filename_stem, response_text):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(LOCAL_RESPONSE_DIR, f"{ts}_{filename_stem}_response.json")

    with open(out_path, "w") as f:
        f.write(response_text.strip() + "\n")

    return out_path


def log_ingest_result(filename, response_text, saved_packet_path):
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        data = {
            "status": "error",
            "data": {
                "transcript_path": None,
                "summary_path": None
            },
            "errors": [{"message": "Invalid JSON response"}]
        }

    entry = {
        "timestamp": datetime.now().isoformat(),
        "source_filename": filename,
        "status": data.get("status"),
        "transcript_path": data.get("data", {}).get("transcript_path"),
        "summary_path": data.get("data", {}).get("summary_path"),
        "response_packet_path": saved_packet_path
    }

    with open(LOCAL_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def send_audio_to_forge(local_file, chat_id, user_id, case_id=None, notes=None, tags=None):
    if not os.path.exists(local_file):
        raise FileNotFoundError(f"Missing local file: {local_file}")

    ensure_dirs()

    filename = os.path.basename(local_file)
    filename_stem = os.path.splitext(filename)[0]

    remote_file = f"{REMOTE_TMP_DIR}/{filename}"
    remote_request = f"{REMOTE_TMP_DIR}/{filename_stem}_request.json"

    request = {
        "source": "val0",
        "job_type": "ingest_audio",
        "chat_id": chat_id,
        "user_id": user_id,
        "case_id": case_id,
        "file_path": remote_file,
        "original_filename": filename,
        "timestamp": datetime.now().isoformat(),
        "context": {
            "notes": notes,
            "tags": tags or []
        }
    }

    local_request = f"/tmp/{filename_stem}_request.json"
    with open(local_request, "w") as f:
        json.dump(request, f, indent=2)

    subprocess.run(["scp", local_file, f"{FORGE_HOST}:{remote_file}"], check=True)
    subprocess.run(["scp", local_request, f"{FORGE_HOST}:{remote_request}"], check=True)

    result = subprocess.run(
        ["ssh", FORGE_HOST, f"{REMOTE_TRIGGER} {remote_request}"],
        capture_output=True,
        text=True,
        check=True
    )

    saved_path = save_response_packet(filename_stem, result.stdout)
    log_ingest_result(filename, result.stdout, saved_path)

    return result.stdout, saved_path


if __name__ == "__main__":
    test_file = "/opt/val0/test_audio.mp3"

    output, saved_path = send_audio_to_forge(
        local_file=test_file,
        chat_id="test_chat",
        user_id="test_user",
        case_id=None,
        notes="helper module test",
        tags=["test"]
    )

    print(output)
    print(f"Saved response packet: {saved_path}")
    print(f"Log updated: {LOCAL_LOG_PATH}")

