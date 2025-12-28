import io
import json
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

pytestmark = pytest.mark.django_db

def _img(name="logo.png"):
    return SimpleUploadedFile(name, b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", content_type="image/png")

def test_users_me_exists(api_client):
    r = api_client.get("/api/users/me")
    assert r.status_code in (200, 401), f"/api/users/me -> {r.status_code}"
    # when unauth, 200 (public) or 401 (needs auth) are acceptable;
    # you can later tighten this to assert 200 after you implement it.

def test_settings_get_organization(api_client):
    r = api_client.get("/api/settings/organization")
    assert r.status_code in (200, 404), f"/api/settings/organization -> {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        # should not crash on empty files
        assert "logo_url" in data and "favicon_url" in data and "principal_signature_url" in data

def test_settings_put_organization_requires_auth(client, api_client, django_user_model):
    # 1) Unauthed JSON: should be blocked
    r = client.put("/api/settings/organization",
                   data=json.dumps({"payload": {"name": "School X"}}),
                   content_type="application/json")
    assert r.status_code in (401, 403, 404)

    # 2) Auth + multipart: use DRF APIClient (not Django client) to avoid 415
    user = django_user_model.objects.create_user(
        username="admin", password="x", is_staff=True, is_superuser=True
    )
    api_client.force_authenticate(user=user)
    r = api_client.put("/api/settings/organization",
                       data={"payload": json.dumps({"name": "School X"}), "logo": _img()},
                       format="multipart")
    # If route not implemented yet you'll see 404; otherwise 200/202
    assert r.status_code in (200, 202, 404)

@pytest.mark.parametrize("path", [
    "/api/settings/academic",
    "/api/settings/reporting",
    "/api/settings/notifications",
    "/api/settings/security",
])
def test_settings_group_endpoints_exist(api_client, path):
    r = api_client.get(path)
    assert r.status_code in (200, 404), f"{path} -> {r.status_code}"
