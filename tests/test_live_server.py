import os
import requests

BASE_URL = "http://127.0.0.1:5000"

def test_live_server():
    print("Testing live running server at:", BASE_URL)
    
    # 1. Test Static HTML Serving
    pages = ["/", "/login.html", "/register.html", "/dashboard.html", "/upload.html", "/reconciliation.html", "/history.html", "/profile.html"]
    for page in pages:
        res = requests.get(f"{BASE_URL}{page}")
        print(f"  [HTML] {page} -> Status {res.status_code}")
        assert res.status_code == 200, f"Failed loading {page}"

    # 2. Test Health Endpoints
    h_res = requests.get(f"{BASE_URL}/health")
    print("  [API] /health ->", h_res.json())
    assert h_res.status_code == 200

    db_res = requests.get(f"{BASE_URL}/db-health")
    print("  [API] /db-health ->", db_res.json())
    assert db_res.status_code == 200

    # 3. Test Authentication (Login)
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@finance.ai",
        "password": "password123"
    })
    print("  [API] /api/auth/login -> Status", login_res.status_code)
    assert login_res.status_code == 200
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Test Dashboard Metrics API
    dash_res = requests.get(f"{BASE_URL}/api/dashboard")
    print("  [API] /api/dashboard -> Total Invoices:", dash_res.json()["metrics"]["total_invoices"])
    assert dash_res.status_code == 200
    assert dash_res.json()["metrics"]["total_invoices"] >= 5

    # 5. Test Reconciliation Inspector API
    recon_res = requests.get(f"{BASE_URL}/api/reconciliation/1", headers=headers)
    print("  [API] /api/reconciliation/1 -> Status:", recon_res.json()["reconciliation"]["status"], "| Risk:", recon_res.json()["reconciliation"]["risk_score"])
    assert recon_res.status_code == 200

    # 6. Test History API
    hist_res = requests.get(f"{BASE_URL}/api/history")
    print("  [API] /api/history -> Count:", hist_res.json()["count"])
    assert hist_res.status_code == 200

    # 7. Test PDF File Upload Pipeline with sample PDF
    sample_pdf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample_data", "invoices", "1_perfect_match_INV-2026-001.pdf")
    if os.path.exists(sample_pdf):
        with open(sample_pdf, "rb") as f:
            upload_res = requests.post(f"{BASE_URL}/api/invoices/upload", files={"file": f})
            print("  [API] /api/invoices/upload -> Status:", upload_res.status_code, "| Recon:", upload_res.json().get("reconciliation", {}).get("status"))
            assert upload_res.status_code == 201

    # 8. Test Human Approval Workflow
    approve_res = requests.post(f"{BASE_URL}/api/reconciliation/1/approve", headers=headers, json={
        "notes": "Verified by Senior Controller."
    })
    print("  [API] /api/reconciliation/1/approve -> Status:", approve_res.status_code, "| Human Action:", approve_res.json()["reconciliation"]["human_action"])
    assert approve_res.status_code == 200
    assert approve_res.json()["reconciliation"]["human_action"] == "APPROVED"

    print("\n[ALL LIVE E2E INTEGRATION CHECKS PASSED SUCCESSFULLY!]")

if __name__ == "__main__":
    test_live_server()
