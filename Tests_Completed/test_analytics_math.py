import pytest
pytestmark = pytest.mark.django_db

def test_overview_avg_math(api_client, seed_minimal):
    sid = seed_minimal["session"].id
    r = api_client.get(f"/api/analytics/session/{sid}/overview")
    assert r.status_code == 200, f"overview -> {r.status_code}"
    data = r.json()
    # Given seed marks_obtained=70/100 for all students, avg should be ~70
    avg = data.get("avg_score")
    assert avg is not None, "avg_score missing in overview payload"
    assert 65 <= float(avg) <= 75, f"expected ~70, got {avg}"

def test_distribution_and_trends_shapes(api_client, seed_minimal):
    sid = seed_minimal["session"].id
    subject_id = seed_minimal["subject"].id

    # distribution(s)
    r = api_client.get(f"/api/analytics/session/{sid}/distribution")
    if r.status_code == 404:
        r = api_client.get(f"/api/analytics/session/{sid}/distributions")  # alias
    assert r.status_code == 200, f"distribution(s) -> {r.status_code}"
    dist = r.json()
    assert isinstance(dist, dict), "distribution payload must be an object"
    assert any(k in dist for k in ("buckets", "series", "labels")), "distribution keys missing"

    # trends
    r = api_client.get(f"/api/analytics/session/{sid}/trends?subject={subject_id}")
    assert r.status_code == 200, f"trends -> {r.status_code}"
    tr = r.json()
    assert isinstance(tr, dict), "trends payload must be an object"
    assert any(k in tr for k in ("series", "points", "labels")), "trends keys missing"
