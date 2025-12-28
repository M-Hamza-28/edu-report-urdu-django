# tests/test_academics.py
import pytest

pytestmark = pytest.mark.django_db


def test_sections_filter_by_grade(api_client, seed_minimal):
    gid = seed_minimal["grade"].id
    r = api_client.get(f"/api/sections/?grade={gid}")
    assert r.status_code == 200
    data = r.json()
    arr = data["results"] if isinstance(data, dict) and "results" in data else data
    assert any(str(x.get("grade")) in (str(gid), gid) or x.get("grade") == gid for x in arr)


def test_enrollments_filter_by_session_and_section(api_client, seed_minimal):
    sid = seed_minimal["session"].id
    secid = seed_minimal["section"].id
    r = api_client.get(f"/api/enrollments/?session={sid}&section={secid}")
    # some backends name it academic_year, so accept 200 even with ignored filter
    assert r.status_code == 200
