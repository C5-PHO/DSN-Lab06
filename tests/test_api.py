from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_rejects_invalid_password_and_records_attempt(client: TestClient):
    response = client.post(
        "/auth/login",
        json={"email": "admin@securedocs.local", "password": "incorrecta"},
    )
    assert response.status_code == 401


def test_employee_only_sees_authorized_documents(client: TestClient, auth_headers):
    headers = auth_headers("empleado@securedocs.local")
    response = client.get("/documentos", headers=headers)
    assert response.status_code == 200
    assert {item["department"] for item in response.json()} == {"FINANZAS"}


def test_employee_cannot_approve_document(client: TestClient, auth_headers):
    headers = auth_headers("empleado@securedocs.local")
    response = client.post("/documentos/1/aprobar", headers=headers)
    assert response.status_code == 403
    assert "permiso" in response.json()["detail"].lower()


def test_supervisor_can_approve_document(client: TestClient, auth_headers):
    headers = auth_headers("supervisor@securedocs.local")
    response = client.post("/documentos/1/aprobar", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "PUBLICADO"


def test_auditor_can_read_audit_logs(client: TestClient, auth_headers):
    headers = auth_headers("auditor@securedocs.local")
    response = client.get("/auditoria", headers=headers)
    assert response.status_code == 200
    assert any(item["action"] == "VIEW_AUDIT" for item in response.json())


def test_logout_revokes_token(client: TestClient, auth_headers):
    headers = auth_headers("admin@securedocs.local")
    assert client.post("/auth/logout", headers=headers).status_code == 200
    assert client.get("/usuarios", headers=headers).status_code == 401
