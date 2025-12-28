# tests/test_settings_contract.py
import pytest

pytestmark = pytest.mark.django_db

@pytest.mark.parametrize("path", [
    "/api/users/me",
    "/api/settings/organization",
    "/api/settings/academic",
    "/api/settings/reporting",
    "/api/settings/notifications",
    "/api/settings/security",
])
def test_settings_contract_exists(api_client, path):
    r = api_client.get(path)
    # Accept 200 (implemented) or 404 (missing) — we want a clear report
    assert r.status_code in (200, 404), f"{path} -> {r.status_code}"
    if r.status_code == 404:
        # Fail with a message so you know it's not wired yet
        pytest.fail(f"Missing endpoint: {path} (wire it in reports/urls.py & views.py)")
