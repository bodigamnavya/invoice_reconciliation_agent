import unittest
import json
from backend.app import create_app
from backend.models.database import SessionLocal, init_db
from backend.models.invoice_model import Invoice
from backend.models.purchase_order_model import PurchaseOrder
from backend.models.payment_model import Payment
from backend.models.vendor_model import Vendor
from backend.models.reconciliation_model import ReconciliationResult
from backend.agents.invoice_agent import InvoiceAgent
from backend.agents.matching_agent import MatchingAgent
from backend.agents.payment_agent import PaymentAgent
from backend.agents.risk_agent import RiskAgent
from backend.agents.decision_agent import DecisionAgent
from backend.services.reconciliation_service import ReconciliationService

class TestReconciliationPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        init_db()

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_invoice_agent_extraction(self):
        sample_text = """
        TAX INVOICE
        Apex Global Technologies
        Tech Park Phase 2, Bangalore, India
        Invoice Number: INV-2026-TEST
        Invoice Date: 2026-08-15
        Purchase Order: PO-2026-101
        Payment Due: 2026-09-15

        Item Description Qty Unit Price (INR) Total (INR)
        Enterprise Cloud Consulting 1 100,000.00 100,000.00
        DevOps Modernization 1 50,000.00 50,000.00

        Subtotal: 127,118.64
        GST / Tax (18%): 22,881.36
        Total Amount Due: 150,000.00
        """
        extracted = InvoiceAgent.extract_structured_data(sample_text)
        self.assertEqual(extracted["invoice_number"], "INV-2026-TEST")
        self.assertEqual(extracted["vendor_name"], "Apex Global Technologies")
        self.assertEqual(extracted["po_number"], "PO-2026-101")
        self.assertEqual(extracted["total_amount"], 150000.00)

    def test_perfect_match_scenario(self):
        inv = self.db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-001").first()
        self.assertIsNotNone(inv, "Seed invoice INV-2026-001 must exist")
        
        recon = ReconciliationService.run_reconciliation(inv.id, self.db)
        self.assertEqual(recon.status, "MATCHED")
        self.assertEqual(recon.po_match_status, "MATCHED")
        self.assertEqual(recon.payment_match_status, "FULL_PAYMENT")
        self.assertEqual(recon.risk_level, "LOW")

    def test_payment_mismatch_scenario(self):
        inv = self.db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-002").first()
        self.assertIsNotNone(inv, "Seed invoice INV-2026-002 must exist")

        recon = ReconciliationService.run_reconciliation(inv.id, self.db)
        self.assertEqual(recon.status, "REVIEW_REQUIRED")
        self.assertEqual(recon.payment_match_status, "PARTIAL_PAYMENT")
        self.assertIn("lower", recon.ai_reason.lower())

    def test_po_mismatch_scenario(self):
        inv = self.db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-003").first()
        self.assertIsNotNone(inv, "Seed invoice INV-2026-003 must exist")

        recon = ReconciliationService.run_reconciliation(inv.id, self.db)
        self.assertEqual(recon.po_match_status, "MISMATCH")
        self.assertIn(recon.status, ["HIGH_RISK", "REVIEW_REQUIRED"])

    def test_duplicate_scenario(self):
        dupe_invs = self.db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-004").all()
        self.assertGreaterEqual(len(dupe_invs), 2, "Must have original and duplicate invoice")
        
        second_inv = dupe_invs[1]
        recon = ReconciliationService.run_reconciliation(second_inv.id, self.db)
        self.assertEqual(recon.duplicate_status, "DUPLICATE_FOUND")
        self.assertGreaterEqual(recon.risk_score, 45)

    def test_statistical_anomaly_scenario(self):
        inv = self.db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-005").first()
        self.assertIsNotNone(inv, "Seed invoice INV-2026-005 must exist")

        recon = ReconciliationService.run_reconciliation(inv.id, self.db)
        self.assertEqual(recon.anomaly_status, "ANOMALY_DETECTED")
        self.assertIn(recon.risk_level, ["HIGH", "CRITICAL"])

    def test_api_endpoints(self):
        # 1. Health check
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)

        # 2. Dashboard metrics
        res = self.client.get("/api/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("metrics", data)
        self.assertGreaterEqual(data["metrics"]["total_invoices"], 5)

        # 3. Auth login
        res = self.client.post("/api/auth/login", json={
            "email": "admin@finance.ai",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 200)
        auth_data = res.get_json()
        token = auth_data["token"]

        # 4. History API
        res = self.client.get("/api/history")
        self.assertEqual(res.status_code, 200)
        hist_data = res.get_json()
        self.assertTrue(hist_data["success"])
        self.assertGreaterEqual(len(hist_data["history"]), 5)

        # 5. Human Approval Action
        inv = self.db.query(Invoice).filter(Invoice.invoice_number == "INV-2026-001").first()
        res = self.client.post(f"/api/reconciliation/{inv.id}/approve", headers={
            "Authorization": f"Bearer {token}"
        }, json={"notes": "Audited and signed off."})
        self.assertEqual(res.status_code, 200)
        approve_data = res.get_json()
        self.assertEqual(approve_data["reconciliation"]["human_action"], "APPROVED")

if __name__ == "__main__":
    unittest.main()
