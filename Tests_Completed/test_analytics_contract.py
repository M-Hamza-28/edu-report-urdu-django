# tests/test_analytics_contract.py
import pytest

pytestmark = pytest.mark.django_db

def _try_get(client, paths):
    for p in paths:
        r = client.get(p)
        if r.status_code == 200:
            return True, p
    return False, paths

def test_analytics_paths(api_client, seed_minimal):
    sid = seed_minimal["session"].id
    subject_id = seed_minimal["subject"].id

    paths_ok = [
        f"/api/analytics/session/{sid}/overview",
        f"/api/analytics/session/{sid}/subject-difficulty",
        # FE wants 'distribution'; backend currently exposes 'distributions'
        # We try both; test will fail clearly if neither exists.
        f"/api/analytics/session/{sid}/distribution",
        f"/api/analytics/session/{sid}/distributions",
        f"/api/analytics/session/{sid}/trends?subject={subject_id}",
        f"/api/analytics/missing-marks?session={sid}",
        f"/api/analytics/session/{sid}/class-compare",
    ]

    missing = []
    # overview
    ok, tried = _try_get(api_client, [paths_ok[0]])
    if not ok: missing.append(tried)
    # subject difficulty
    ok, tried = _try_get(api_client, [paths_ok[1]])
    if not ok: missing.append(tried)
    # distribution(s)
    ok, tried = _try_get(api_client, [paths_ok[2], paths_ok[3]])
    if not ok: missing.append(tried)
    # trends
    ok, tried = _try_get(api_client, [paths_ok[4]])
    if not ok: missing.append(tried)
    # missing-marks
    ok, tried = _try_get(api_client, [paths_ok[5]])
    if not ok: missing.append(tried)
    # class-compare
    ok, tried = _try_get(api_client, [paths_ok[6]])
    if not ok: missing.append(tried)

    assert not missing, f"Analytics endpoints missing or miswired: {missing}"
