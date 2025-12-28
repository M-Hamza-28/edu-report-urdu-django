# scripts/smoke_backend.py
import os, sys, json, requests
from urllib.parse import urljoin

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/api"

def req(method, path):
    url = urljoin(BASE + "/", path.lstrip("/"))
    try:
        r = requests.request(method, url, timeout=10)
        return r.status_code, r.text[:240]
    except Exception as e:
        return 0, str(e)

def main():
    endpoints = [
        "exam-sessions/", "students/", "subjects/", "grades/", "sections/",
        "enrollments/", "report-templates/", "message-logs/", "feedback/",
    ]
    for p in endpoints:
        st, _ = req("GET", p)
        print(f"GET {p:35} -> {st}")

    # Analytics (FE-expected)
    sid = 1
    for p in [
        f"analytics/session/{sid}/overview",
        f"analytics/session/{sid}/trends?subject=",
        f"analytics/session/{sid}/distribution",
        f"analytics/session/{sid}/distributions",
        f"analytics/session/{sid}/subject-difficulty",
        f"analytics/missing-marks?session={sid}",
        f"analytics/session/{sid}/class-compare",
    ]:
        st, _ = req("GET", p)
        print(f"GET {p:35} -> {st}")

    # Settings / profile
    for p in [
        "users/me",
        "settings/organization",
        "settings/academic",
        "settings/reporting",
        "settings/notifications",
        "settings/security",
    ]:
        st, _ = req("GET", p)
        print(f"GET {p:35} -> {st}")

if __name__ == "__main__":
    main()
