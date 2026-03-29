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


def load_latest_response():
    path = latest_response_file()
    if not path:
        return None, None

    with open(path, "r") as f:
        data = json.load(f)

    return path, data


def extract_response_fields(data):
    return {
        "status": data.get("status"),
        "transcript_path": data.get("data", {}).get("transcript_path"),
        "summary_path": data.get("data", {}).get("summary_path"),
        "notes": data.get("advisory", {}).get("notes"),
        "suggested_tasks": data.get("advisory", {}).get("suggested_tasks", []),
        "errors": data.get("errors", [])
    }


def build_user_message(fields):
    status = fields["status"]
    summary_path = fields["summary_path"]
    suggested_tasks = fields["suggested_tasks"]
    errors = fields["errors"]

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


def get_latest_user_message():
    path, data = load_latest_response()
    if not data:
        return None, "No response packet found."

    fields = extract_response_fields(data)
    message = build_user_message(fields)
    return fields, message


if __name__ == "__main__":
    fields, message = get_latest_user_message()
    print("\n=== LATEST RESPONSE MESSAGE ===\n")
    print(message)
    print("\n===============================\n")

