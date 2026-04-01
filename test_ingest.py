#!/usr/bin/env python3

import os
import json
import subprocess
from datetime import datetime

REQUEST_PATH = "/tmp/test_request.json"
FORGE_COMMAND = "python3 /opt/valprime/trigger_ingest.py"

# change this to a real file that exists on Forge
FILE_PATH = "/home/forge/valeria_ops/ingest/test_audio/test3.mp3"


def main():
    request = {
        "source": "val0",
        "job_type": "ingest_audio",
        "chat_id": "test_chat",
        "user_id": "test_user",
        "case_id": None,
        "file_path": FILE_PATH,
        "original_filename": os.path.basename(FILE_PATH),
        "timestamp": datetime.now().isoformat(),
        "context": {
            "notes": "val0 simulation test",
            "tags": ["test"]
        }
    }

    with open(REQUEST_PATH, "w") as f:
        json.dump(request, f, indent=2)

    print("\n=== SENDING REQUEST TO FORGE ===\n")

    result = subprocess.run(
        f"{FORGE_COMMAND} {REQUEST_PATH}",
        shell=True,
        capture_output=True,
        text=True
    )

    print(result.stdout)


if __name__ == "__main__":
    main()

