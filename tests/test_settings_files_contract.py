import io
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

def test_organization_files_put_returns_urls():
    client = APIClient()
    # Anonymous GET should be allowed
    res = client.get("/api/settings/organization")
    assert res.status_code == 200

    # Auth required for PUT
    client.force_authenticate(user=None)  # ensure not authenticated
    res = client.put("/api/settings/organization", {"payload": {}}, format="json")
    assert res.status_code in (401, 403)

    # Now authenticate and send multipart
    from django.contrib.auth import get_user_model
    u = get_user_model().objects.create_superuser("admin2", "a@b.c", "x")
    client.force_authenticate(user=u)

    logo = SimpleUploadedFile("logo.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
    fav = SimpleUploadedFile("favicon.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
    sig = SimpleUploadedFile("sig.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")

    res = client.put("/api/settings/organization", data={
        "payload": '{"school_name":"Test"}',
        "logo": logo,
        "favicon": fav,
        "principal_signature": sig,
    }, format="multipart")

    assert res.status_code == 200
    body = res.json()
    for k in ("logo_url", "favicon_url", "principal_signature_url"):
        assert k in body
        assert isinstance(body[k], str)
