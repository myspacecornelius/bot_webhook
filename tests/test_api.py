"""
API integration tests using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient

from phantom.api.routes import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


# ── Status Endpoints ──────────────────────────────────────────


class TestStatusEndpoints:
    def test_get_status(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "running" in data or "tasks" in data

    def test_swagger_docs(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_json(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "paths" in schema
        assert "/api/status" in schema["paths"]


# ── Task CRUD ─────────────────────────────────────────────────


class TestTaskCRUD:
    def test_list_tasks(self, client):
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        assert "tasks" in resp.json()

    def test_create_task(self, client):
        resp = client.post(
            "/api/tasks",
            json={
                "site_name": "TestShop",
                "site_url": "https://testshop.com",
                "monitor_input": "Test Product",
            },
        )
        assert resp.status_code == 200
        assert "id" in resp.json()

    def test_create_and_delete_task(self, client):
        create = client.post(
            "/api/tasks",
            json={
                "site_name": "TestShop",
                "site_url": "https://testshop.com",
                "monitor_input": "Test Product",
            },
        )
        task_id = create.json()["id"]

        delete = client.delete(f"/api/tasks/{task_id}")
        assert delete.status_code == 200

    def test_delete_nonexistent_task(self, client):
        resp = client.delete("/api/tasks/fake-id-999")
        assert resp.status_code == 404


# ── Error Handling ────────────────────────────────────────────


class TestErrorHandling:
    def test_not_found_returns_404(self, client):
        resp = client.post("/api/tasks/nonexistent/stop")
        assert resp.status_code == 404

    def test_response_has_request_id(self, client):
        resp = client.get("/api/status")
        assert "X-Request-ID" in resp.headers


# ── Webhook Endpoints ─────────────────────────────────────────


class TestWebhooks:
    def test_receive_webhook(self, client):
        resp = client.post(
            "/api/webhooks/shopify",
            json={"event_type": "orders/create", "order_id": 123},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

    def test_webhook_idempotency(self, client):
        headers = {"X-Idempotency-Key": "test-key-abc"}
        payload = {"event_type": "test"}

        resp1 = client.post("/api/webhooks/test", json=payload, headers=headers)
        assert resp1.status_code == 200

        resp2 = client.post("/api/webhooks/test", json=payload, headers=headers)
        assert resp2.status_code == 409  # DuplicateError

    def test_webhook_stats(self, client):
        resp = client.get("/api/webhooks/stats")
        assert resp.status_code == 200
        assert "total_received" in resp.json()

    def test_webhook_events(self, client):
        resp = client.get("/api/webhooks/events")
        assert resp.status_code == 200
        assert "events" in resp.json()


# ── Profiles ──────────────────────────────────────────────────


class TestProfiles:
    def test_list_profiles(self, client):
        resp = client.get("/api/profiles")
        assert resp.status_code == 200

    def test_create_profile(self, client):
        resp = client.post(
            "/api/profiles",
            json={
                "name": "Test Profile",
                "email": "test@example.com",
                "shipping_first_name": "John",
                "shipping_last_name": "Doe",
                "shipping_address1": "123 Main St",
                "shipping_city": "New York",
                "shipping_state": "NY",
                "shipping_zip": "10001",
                "card_holder": "John Doe",
                "card_number": "4111111111111111",
                "card_expiry": "12/30",
                "card_cvv": "123",
            },
        )
        assert resp.status_code == 200
        assert "id" in resp.json()


# ── Monitors ──────────────────────────────────────────────────


class TestMonitors:
    def test_monitor_status(self, client):
        resp = client.get("/api/monitors/status")
        assert resp.status_code == 200

    def test_monitor_events(self, client):
        resp = client.get("/api/monitors/events")
        assert resp.status_code == 200
        assert "events" in resp.json()

    def test_analytics(self, client):
        resp = client.get("/api/analytics/checkout")
        assert resp.status_code == 200
        assert "total_tasks" in resp.json()
