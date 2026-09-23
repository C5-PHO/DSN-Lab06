from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["SECUREDOCS_DATABASE_URL"] = "sqlite:///./test_secure_docs.db"
os.environ["SECUREDOCS_SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"

from app.main import app  # noqa: E402

TEST_DB = Path("test_secure_docs.db")


@pytest.fixture(scope="session", autouse=True)
def clean_test_database():
    TEST_DB.unlink(missing_ok=True)
    yield
    TEST_DB.unlink(missing_ok=True)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers(client: TestClient):
    def _login(email: str) -> dict[str, str]:
        response = client.post(
            "/auth/login",
            json={"email": email, "password": "Secure123!"},
            headers={"X-Device": "CORPORATIVO", "X-Location": "PERU"},
        )
        assert response.status_code == 200, response.text
        return {
            "Authorization": f"Bearer {response.json()['access_token']}",
            "X-Device": "CORPORATIVO",
            "X-Location": "PERU",
            "X-Access-Time": "2026-09-23T11:30:00-05:00",
        }

    return _login
