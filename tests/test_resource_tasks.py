"""Tests for the /tasks endpoints.

These endpoints talk to Celery/Redis (see tasks_bp.py), so the real broker
and result backend are replaced with lightweight fakes via monkeypatch -
these tests exercise the Flask view logic without requiring a running
Redis/Celery worker.
"""

import tasks_bp


class FakeAsyncJob:
    def __init__(self, task_id):
        self.id = task_id


class FakeAsyncResult:
    def __init__(self, task_id, app=None):
        self.task_id = task_id
        self.state = FakeAsyncResult.next_state
        self.result = FakeAsyncResult.next_result
        self.info = FakeAsyncResult.next_info

    next_state = "PENDING"
    next_result = None
    next_info = None


def test_add_numbers_enqueues_a_task(client, monkeypatch):
    captured = {}

    def fake_delay(a, b):
        captured["args"] = (a, b)
        return FakeAsyncJob("task-123")

    monkeypatch.setattr(tasks_bp.add, "delay", fake_delay)

    response = client.post("/tasks/add", json={"a": 2, "b": 3})

    assert response.status_code == 202
    assert response.get_json() == {"task_id": "task-123", "status": "PENDING"}
    assert captured["args"] == (2, 3)


def test_add_numbers_defaults_missing_values_to_zero(client, monkeypatch):
    captured = {}

    def fake_delay(a, b):
        captured["args"] = (a, b)
        return FakeAsyncJob("task-456")

    monkeypatch.setattr(tasks_bp.add, "delay", fake_delay)

    response = client.post("/tasks/add", json={})

    assert response.status_code == 202
    assert captured["args"] == (0, 0)


def test_task_status_reports_success(client, monkeypatch):
    FakeAsyncResult.next_state = "SUCCESS"
    FakeAsyncResult.next_result = 5
    monkeypatch.setattr(tasks_bp, "AsyncResult", FakeAsyncResult)

    response = client.get("/tasks/status/task-123")

    assert response.status_code == 200
    body = response.get_json()
    assert body == {"task_id": "task-123", "state": "SUCCESS", "result": 5}


def test_task_status_reports_failure(client, monkeypatch):
    FakeAsyncResult.next_state = "FAILURE"
    FakeAsyncResult.next_info = RuntimeError("boom")
    monkeypatch.setattr(tasks_bp, "AsyncResult", FakeAsyncResult)

    response = client.get("/tasks/status/task-123")

    assert response.status_code == 200
    body = response.get_json()
    assert body["task_id"] == "task-123"
    assert body["state"] == "FAILURE"
    assert "boom" in body["error"]


def test_task_status_reports_pending(client, monkeypatch):
    FakeAsyncResult.next_state = "PENDING"
    FakeAsyncResult.next_result = None
    FakeAsyncResult.next_info = None
    monkeypatch.setattr(tasks_bp, "AsyncResult", FakeAsyncResult)

    response = client.get("/tasks/status/unknown-task")

    assert response.status_code == 200
    assert response.get_json() == {"task_id": "unknown-task", "state": "PENDING"}
