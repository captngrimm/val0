#!/usr/bin/env python3

import os
import json
import glob

RESPONSE_DIR = "/opt/val0/forge_responses"


def latest_response_file():
    files = glob.glob(os.path.join(RESPONSE_DIR, "*_response.json"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def main():
    path = latest_response_file()
    if not path:
        print("No response packet found.")
        return

    with open(path, "r") as f:
        data = json.load(f)

    status = data.get("status")
    transcript_path = data.get("data", {}).get("transcript_path")
    summary_path = data.get("data", {}).get("summary_path")
    notes = data.get("advisory", {}).get("notes")
    suggested_tasks = data.get("advisory", {}).get("suggested_tasks", [])
    errors = data.get("errors", [])

    print("\n=== FORGE RESPONSE ===\n")
    print(f"Packet: {path}")
    print(f"Status: {status}")
    print(f"Transcript: {transcript_path}")
    print(f"Summary: {summary_path}")
    print(f"Notes: {notes}")
    print(f"Suggested Tasks: {suggested_tasks}")
    print(f"Errors: {errors}")
    print("\n======================\n")


if __name__ == "__main__":
    main()

