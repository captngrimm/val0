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


def build_user_message(data):
    status = data.get("status")
    summary_path = data.get("data", {}).get("summary_path")
    suggested_tasks = data.get("advisory", {}).get("suggested_tasks", [])
    errors = data.get("errors", [])

    if status == "success":
        parts = ["Audio processed successfully."]

        if summary_path:
            parts.append(f"Summary saved: {summary_path}")

        if suggested_tasks:
            parts.append("Suggested tasks:")
            parts.extend([f"- {task}" for task in suggested_tasks])

        return "\n".join(parts)

    if status == "skipped":
        return "Audio was already processed. No new action taken."

    if status == "error":
        if errors:
            return f"Audio processing failed: {errors[0].get('message', 'unknown error')}"
        return "Audio processing failed."

    return "Unknown response state."


def main():
    path = latest_response_file()
    if not path:
        print("No response packet found.")
        return

    with open(path, "r") as f:
        data = json.load(f)

    print("\n=== USER MESSAGE ===\n")
    print(build_user_message(data))
    print("\n====================\n")


if __name__ == "__main__":
    main()

