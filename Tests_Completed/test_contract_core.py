# tests/test_contract_core.py
import pytest

pytestmark = pytest.mark.django_db


def test_core_lists_exist_and_return_200(api_client, seed_minimal):
    paths = [
        "/api/exam-sessions/",
        "/api/students/",
        "/api/subjects/",
        "/api/grades/",
        "/api/sections/",
        "/api/enrollments/",
        "/api/report-templates/",
        "/api/message-logs/",
        "/api/feedback/",
    ]
    for p in paths:
        r = api_client.get(p)
        assert r.status_code == 200, f"{p} -> {r.status_code} {r.content[:200]}"
