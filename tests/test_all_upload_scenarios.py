import os
import io
import unittest
from backend.app import create_app
from backend.models.database import SessionLocal, init_db
from database.seed_data import seed_database

class TestAllUploadScenarios(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        seed_database()

    def _upload_pdf(self, filename):
        pdf_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "invoices", filename)
        self.assertTrue(os.path.exists(pdf_path), f"File {pdf_path} must exist")
        with open(pdf_path, "rb") as f:
            data = {"file": (f, filename)}
            return self.client.post("/api/invoices/upload", data=data, content_type="multipart/form-data")

    def test_upload_scenario_1_perfect_match(self):
        res = self._upload_pdf("1_perfect_match_INV-2026-001.pdf")
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        inv = data["invoice"]
        recon = data["reconciliation"]
        
        # Verify accurate amount extraction (NOT ₹0.00)
        self.assertEqual(inv["total_amount"], 150000.00)
        self.assertEqual(inv["subtotal"], 127118.64)
        self.assertEqual(inv["tax_amount"], 22881.36)
        
        # Verify 3-way reconciliation
        self.assertEqual(recon["status"], "MATCHED")
        self.assertEqual(recon["po_match_status"], "MATCHED")
        self.assertEqual(recon["payment_match_status"], "FULL_PAYMENT")
        self.assertEqual(recon["duplicate_status"], "UNIQUE")
        self.assertEqual(recon["anomaly_status"], "NORMAL")
        self.assertEqual(recon["risk_level"], "LOW")
        self.assertEqual(recon["risk_score"], 0)

    def test_upload_scenario_2_payment_mismatch(self):
        res = self._upload_pdf("2_payment_mismatch_INV-2026-002.pdf")
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        inv = data["invoice"]
        recon = data["reconciliation"]

        self.assertEqual(inv["total_amount"], 85000.00)
        self.assertEqual(recon["status"], "REVIEW_REQUIRED")
        self.assertEqual(recon["payment_match_status"], "PARTIAL_PAYMENT")
        self.assertEqual(recon["amount_difference_payment"], -5000.00)

    def test_upload_scenario_3_po_mismatch(self):
        res = self._upload_pdf("3_po_mismatch_INV-2026-003.pdf")
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        inv = data["invoice"]
        recon = data["reconciliation"]

        self.assertEqual(inv["total_amount"], 90000.00)
        self.assertEqual(recon["status"], "HIGH_RISK")
        self.assertEqual(recon["po_match_status"], "MISMATCH")
        self.assertEqual(recon["amount_difference_po"], 5000.00)

    def test_upload_scenario_4_duplicate_invoice(self):
        res = self._upload_pdf("4_duplicate_invoice_INV-2026-004.pdf")
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        recon = data["reconciliation"]

        self.assertEqual(recon["duplicate_status"], "DUPLICATE_FOUND")
        self.assertIn(recon["status"], ["REJECT", "REVIEW_REQUIRED"])
        self.assertIn(recon["risk_level"], ["HIGH", "CRITICAL"])

    def test_upload_scenario_5_unusual_amount_anomaly(self):
        res = self._upload_pdf("5_anomaly_unusual_amount_INV-2026-005.pdf")
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        inv = data["invoice"]
        recon = data["reconciliation"]

        self.assertEqual(inv["total_amount"], 320000.00)
        self.assertEqual(recon["anomaly_status"], "ANOMALY_DETECTED")
        self.assertEqual(recon["status"], "HIGH_RISK")
        self.assertIn(recon["risk_level"], ["HIGH", "CRITICAL"])

if __name__ == "__main__":
    unittest.main()
