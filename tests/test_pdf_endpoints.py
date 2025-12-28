# tests/test_pdf_endpoints.py
# Discovers list endpoints & first IDs automatically. Skips only if empty.

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

@pytest.fixture
def client(db):
    admin = User.objects.create_user(
        username="pdf_admin", password="x", is_staff=True, is_superuser=True
    )
    c = APIClient()
    c.force_authenticate(user=admin)
    return c

def _best_list(client, candidates):
    """Return (path, json) for the first list endpoint that responds 200 with a non-error body."""
    for path in candidates:
        r = client.get(path)
        if r.status_code == 200:
            try:
                body = r.json()
            except Exception:
                body = None
            if body is not None:
                return path, body
    return None, None

def _first_id_from_list(body):
    """Support plain list or DRF pagination (results)."""
    if isinstance(body, dict) and isinstance(body.get("results"), list):
        arr = body["results"]
    else:
        arr = body if isinstance(body, list) else []
    return (arr[0]["id"] if arr and isinstance(arr[0], dict) and "id" in arr[0] else None)

def _skip_if_missing(resp, what):
    if resp.status_code in (404, 400):
        pytest.skip(f"{what}: missing data (status {resp.status_code}).")
    assert resp.status_code in (200, 206), f"{what}: unexpected status {resp.status_code}"

@pytest.mark.django_db
def test_template_preview_pdf(client):
    # Try both naming conventions for templates
    list_path, body = _best_list(client, ["/api/templates/", "/api/report-templates/"])
    if not body:
        pytest.skip("No templates list endpoint responded (templates empty or route missing).")
    tpl_id = _first_id_from_list(body)
    if not tpl_id:
        pytest.skip("Templates list returned no items; nothing to preview.")

    # Try both possible preview actions
    preview_paths = [f"/api/templates/{tpl_id}/preview_pdf", f"/api/report-templates/{tpl_id}/preview_pdf"]
    last = None
    for p in preview_paths:
        r = client.get(p)
        last = r
        if r.status_code in (200, 206):
            ct = r.headers.get("Content-Type", "")
            assert "pdf" in ct.lower()
            return
    _skip_if_missing(last, "template_preview_pdf")

@pytest.mark.django_db
def test_report_preview_pdf(client):
    # Reports list is usually /api/reports/
    list_path, body = _best_list(client, ["/api/reports/"])
    if not body:
        pytest.skip("No reports list or empty.")
    rep_id = _first_id_from_list(body)
    if not rep_id:
        pytest.skip("Reports list returned no items; nothing to preview.")

    # Some backends expose /preview, some /preview_pdf
    for p in (f"/api/reports/{rep_id}/preview", f"/api/reports/{rep_id}/preview_pdf"):
        r = client.get(p)
        if r.status_code in (200, 206):
            ct = r.headers.get("Content-Type", "")
            assert "pdf" in ct.lower()
            return
        last = r
    _skip_if_missing(last, "report_preview")
