#!/usr/bin/env python3

import os
import json
import subprocess
from datetime import datetime

FORGE_HOST = "forge@100.88.212.83"
REMOTE_TRIGGER = "python3 /opt/valprime/trigger_ingest.py"
REMOTE_TMP_DIR = "/tmp"


def send_audio_to_forge(local_file, chat_id, user_id, case_id=None, notes=None, tags=None):
    if not os.path.exists(local_file):
        raise FileNotFoundError(f"Missing local file: {local_file}")

    filename = os.path.basename(local_file)
    remote_file = f"{REMOTE_TMP_DIR}/{filename}"
    remote_request = f"{REMOTE_TMP_DIR}/{os.path.splitext(filename)[0]}_request.json"

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

    local_request = f"/tmp/{os.path.splitext(filename)[0]}_request.json"
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

    return result.stdout


if __name__ == "__main__":
    test_file = "/opt/val0/test_audio.mp3"
    output = send_audio_to_forge(
        local_file=test_file,
        chat_id="test_chat",
        user_id="test_user",
        case_id=None,
        notes="helper module test",
        tags=["test"]
    )
    print(output)

