from flask import Flask, request, jsonify, abort

from db import init_db, get_connection

app = Flask(__name__)
init_db()

VALID_PRIORITIES = {"low", "normal", "high"}


@app.route("/tasks", methods=["GET"])
def list_tasks():
    limit = int(request.args.get("limit", 20))
    offset = int(request.args.get("offset", 0))
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, done, priority FROM tasks ORDER BY id LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    if not title:
        abort(400, "title is required")
    priority = data.get("priority", "normal")
    if priority not in VALID_PRIORITIES:
        abort(400, f"priority must be one of {sorted(VALID_PRIORITIES)}")
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (title, priority) VALUES (?, ?)", (title, priority)
        )
        conn.commit()
        task_id = cur.lastrowid
    return jsonify({"id": task_id, "title": title, "done": 0, "priority": priority}), 201


@app.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    data = request.get_json(force=True)
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET done = ? WHERE id = ?",
            (int(bool(data.get("done", False))), task_id),
        )
        conn.commit()
    return jsonify({"status": "updated"})


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)
