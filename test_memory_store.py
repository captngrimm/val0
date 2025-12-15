from memory_store import init_db, save_message, get_recent_messages


def main() -> None:
    chat_id = 123456
    print("Initializing DB…")
    init_db()

    print("Inserting sample messages…")
    mid1 = save_message(chat_id, "user", "Hola, Val", None, "test-model")
    mid2 = save_message(chat_id, "assistant", "Hola, Boss", 999, "test-model")

    print(f"Inserted IDs: {mid1}, {mid2}")

    print("Fetching recent messages…")
    msgs = get_recent_messages(chat_id, limit=10)
    for m in msgs:
        print(m["id"], m["role"], m["content"])

    print("Done.")


if __name__ == "__main__":
    main()
