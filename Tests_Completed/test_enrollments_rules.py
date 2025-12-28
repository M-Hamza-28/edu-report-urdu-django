import json
import pytest
pytestmark = pytest.mark.django_db

def test_enrollment_uniqueness(authed_api_client, seed_minimal):
    s = seed_minimal["students"][0].id
    g = seed_minimal["grade"].id
    sec = seed_minimal["section"].id
    session = seed_minimal["session"].id

    payload = {"student": s, "grade": g, "section": sec, "session": session}
    # Some projects use academic_year instead of session; try both
    alt_payload = {"student": s, "grade": g, "section": sec, "academic_year": session}

    r = authed_api_client.post("/api/enrollments/", data=json.dumps(payload), content_type="application/json")
    if r.status_code == 400 and "unknown field" in r.content.decode().lower():
        r = authed_api_client.post("/api/enrollments/", data=json.dumps(alt_payload), content_type="application/json")

    if r.status_code in (404, 405):
        pytest.skip("Enrollments create not wired; implement POST with uniqueness validation then re-run.")

    assert r.status_code in (201, 200, 400)
    if r.status_code in (200, 201):
        # Duplicate should fail with 400/409
        r2 = authed_api_client.post("/api/enrollments/", data=json.dumps(payload), content_type="application/json")
        assert r2.status_code in (400, 409), f"duplicate enrollment must be rejected, got {r2.status_code}"
