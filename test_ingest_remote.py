#!/usr/bin/env python3

import os
import json
import subprocess
from datetime import datetime

FORGE_HOST = "forge@100.88.212.83"
REMOTE_REQ = "/tmp/test_request.json"
REMOTE_TRIGGER = "python3 /opt/valprime/trigger_ingest.py /tmp/test_request.json"

# change this to a real audio file that exists on Val0
LOCAL_FILE = "/opt/val0/test_audio.mp3"
REMOTE_FILE = "/tmp/test_audio.mp3"


def main():
    if not os.path.exists(LOCAL_FILE):
        print(f"Missing local file: {LOCAL_FILE}")
        return

    req = {
        "source": "val0",
        "job_type": "ingest_audio",
        "chat_id": "test_chat",
        "user_id": "test_user",
        "case_id": None,
        "file_path": REMOTE_FILE,
        "original_filename": os.path.basename(REMOTE_FILE),
        "timestamp": datetime.now().isoformat(),
        "context": {
            "notes": "remote bridge test",
            "tags": ["test"]
        }
    }

    with open("/tmp/test_request.json", "w") as f:
        json.dump(req, f, indent=2)

    subprocess.run(["scp", LOCAL_FILE, f"{FORGE_HOST}:{REMOTE_FILE}"], check=True)
    subprocess.run(["scp", "/tmp/test_request.json", f"{FORGE_HOST}:{REMOTE_REQ}"], check=True)
    subprocess.run(["ssh", FORGE_HOST, REMOTE_TRIGGER], check=True)


if __name__ == "__main__":
    main()

