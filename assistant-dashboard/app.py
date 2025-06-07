import os
import sys
from flask import Flask, render_template, redirect, request, url_for

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(PROJECT_ROOT, "real-voice-assistant"))
from database import db  # type: ignore  # noqa: E402


app = Flask(__name__)


@app.route("/")
def index():
    tasks = db.list_tasks()
    return render_template("index.html", tasks=tasks)


@app.route("/task/new", methods=["GET", "POST"])
def new_task():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description", "")
        if title:
            db.create_task(title, description)
        return redirect("/")
    return render_template("new_task.html")


@app.route("/task/<int:task_id>/complete")
def complete_task(task_id):
    db.update_task_status(task_id, "completed")
    return redirect("/")


@app.route("/task/<int:task_id>/delete")
def delete_task(task_id):
    """Delete a task from the database."""
    db.update_task_status(task_id, "deleted")
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
