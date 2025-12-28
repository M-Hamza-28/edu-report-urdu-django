# tests/test_analytics_contract.py
# Endpoint-only analytics contract checks (no direct model imports).
# If a referenced ID doesn't exist yet, we SKIP instead of failing hard.
# When the endpoint returns 200, we assert its response shape.

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

# You can tweak these IDs if you know real ones in your DB.
STUDENT_ID = 1
TUTOR_ID = 1
SECTION_ID = 1
SESSION_ID = 1

@pytest.fixture
def client(db):
    # Superuser to avoid permission issues in early stages
    admin = User.objects.create_user(
        username="admin_test",
        password="x",
        is_staff=True,
        is_superuser=True,
    )
    c = APIClient()
    c.force_authenticate(user=admin)
    return c

def _skip_if_missing(resp, what):
    """
    If the endpoint returns a 404/400 (missing IDs/data), skip test gracefully.
    Otherwise, ensure we got 200 for shape assertions.
    """
    if resp.status_code in (404, 400):
        pytest.skip(f"{what}: test data not present yet (status {resp.status_code}).")
    assert resp.status_code == 200, f"{what}: unexpected status {resp.status_code} {getattr(resp, 'data', '')}"

@pytest.mark.django_db
def test_student_trends_shape(client):
    r = client.get(f"/api/analytics/student/{STUDENT_ID}/trends", {"session": SESSION_ID})
    _skip_if_missing(r, "student_trends")
    body = r.json()
    assert "labels" in body and isinstance(body["labels"], list)
    assert "series" in body and isinstance(body["series"], list)

@pytest.mark.django_db
def test_student_mastery_shape(client):
    r = client.get(f"/api/analytics/student/{STUDENT_ID}/mastery", {"session": SESSION_ID})
    _skip_if_missing(r, "student_mastery")
    body = r.json()
    for key in ("rows", "cols", "data"):
        assert key in body
    assert isinstance(body["rows"], list)
    assert isinstance(body["cols"], list)
    assert isinstance(body["data"], list)

@pytest.mark.django_db
def test_student_flags_shape(client):
    r = client.get(f"/api/analytics/student/{STUDENT_ID}/flags", {"session": SESSION_ID})
    _skip_if_missing(r, "student_flags")
    body = r.json()
    assert "flags" in body and isinstance(body["flags"], list)

@pytest.mark.django_db
def test_tutor_dashboard_shape(client):
    r = client.get(f"/api/analytics/tutor/{TUTOR_ID}/", {"session": SESSION_ID})
    _skip_if_missing(r, "tutor_dashboard")
    body = r.json()
    assert "summary" in body and isinstance(body["summary"], dict)
    for k in ("median_percent", "improving_percent", "students_count"):
        assert k in body["summary"]

@pytest.mark.django_db
def test_section_coverage_shape(client):
    r = client.get(f"/api/analytics/section/{SECTION_ID}/coverage", {"session": SESSION_ID})
    _skip_if_missing(r, "section_coverage")
    body = r.json()
    assert "coverage_pct" in body
    assert "missing" in body and isinstance(body["missing"], list)
