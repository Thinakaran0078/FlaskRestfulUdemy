# tasks_bp.py
from flask import jsonify, request
from flask_smorest import Blueprint
from celery.result import AsyncResult
from celery_app import celery
from tasks import add

tasks_blp = Blueprint("tasks", "tasks", url_prefix="/tasks", description="Async tasks")

@tasks_blp.route("/add", methods=["POST"])
def add_numbers():
    payload = request.get_json(silent=True) or {}
    a = int(payload.get("a", 0))
    b = int(payload.get("b", 0))
    job = add.delay(a, b)
    return jsonify({"task_id": job.id, "status": "PENDING"}), 202

@tasks_blp.route("/status/<task_id>", methods=["GET"])
def task_status(task_id):
    res = AsyncResult(task_id, app=celery)
    body = {"task_id": task_id, "state": res.state}
    if res.state == "SUCCESS":
        body["result"] = res.result
    elif res.state == "FAILURE":
        body["error"] = str(res.info)
    return jsonify(body), 200
