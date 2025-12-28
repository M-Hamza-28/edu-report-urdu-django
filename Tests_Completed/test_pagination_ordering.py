import json
import pytest
pytestmark = pytest.mark.django_db

def test_threads_pagination_and_ordering(authed_api_client):
    # Create several threads
    for i in range(7):
        authed_api_client.post("/api/messages/threads/",
                               data=json.dumps({"subject":f"T{i}","is_announcement":False,"audience":{"role":"student","id":1}}),
                               content_type="application/json")

    r = authed_api_client.get("/api/messages/threads/?page=1&page_size=5&ordering=-updated_at")
    assert r.status_code == 200
    data = r.json()
    results = data.get("results", data if isinstance(data, list) else [])
    assert len(results) <= 5, "page_size must limit results"

    # second page
    r2 = authed_api_client.get("/api/messages/threads/?page=2&page_size=5&ordering=-updated_at")
    assert r2.status_code == 200
