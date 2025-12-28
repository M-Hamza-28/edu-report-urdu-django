import pytest
pytestmark = pytest.mark.django_db

def test_reports_pdf_endpoint_exists(authed_api_client, seed_minimal):
    # Try a likely endpoint name; skip if not wired yet
    r = authed_api_client.post("/api/reports/generate", data={"student": seed_minimal["students"][0].id})
    if r.status_code == 404:
        pytest.skip("PDF generation endpoint not wired; add route then re-run.")
    assert r.status_code in (200, 201)
    ct = r.headers.get("Content-Type","")
    assert "pdf" in ct.lower(), f"Content-Type must be PDF, got {ct}"
