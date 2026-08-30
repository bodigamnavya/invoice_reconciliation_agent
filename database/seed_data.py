import json
from datetime import date, timedelta
from backend.models.database import SessionLocal, init_db
from backend.models.user_model import User
from backend.models.vendor_model import Vendor
from backend.models.purchase_order_model import PurchaseOrder
from backend.models.invoice_model import Invoice
from backend.models.payment_model import Payment
from backend.models.reconciliation_model import ReconciliationResult
from backend.services.reconciliation_service import ReconciliationService
from backend.utils.security import hash_password

def seed_database():
    """Populates database with initial users, vendors, POs, payments, and 5 demo reconciliation scenarios."""
    init_db()
    db = SessionLocal()
    try:
        print("[SEED] Seeding database...")
        
        # 1. Clean existing records for fresh deterministic state
        db.query(ReconciliationResult).delete()
        db.query(Payment).delete()
        db.query(Invoice).delete()
        db.query(PurchaseOrder).delete()
        db.query(Vendor).delete()
        db.query(User).delete()
        db.commit()

        # 2. Seed Default Finance Users
        admin_user = User(
            full_name="Navya Sharma",
            email="admin@finance.ai",
            password_hash=hash_password("password123"),
            role="Senior Controller"
        )
        analyst_user = User(
            full_name="Alex Rivera",
            email="analyst@finance.ai",
            password_hash=hash_password("password123"),
            role="Reconciliation Specialist"
        )
        db.add_all([admin_user, analyst_user])
        db.commit()
        db.refresh(admin_user)

        # 3. Seed Vendors
        v1 = Vendor(
            name="Apex Global Technologies",
            tax_id="GSTIN29AAACA0001Z1",
            email="billing@apextech.com",
            phone="+91 80 4123 4567",
            address="Tech Park Phase 2, Bangalore, India",
            average_invoice_amount=150000.00,
            historical_invoice_count=18,
            risk_rating="LOW"
        )
        v2 = Vendor(
            name="Nova Solutions Pvt Ltd",
            tax_id="GSTIN27AABCN1234F1",
            email="finance@novasolutions.in",
            phone="+91 22 6123 7890",
            address="Nariman Point, Mumbai, India",
            average_invoice_amount=85000.00,
            historical_invoice_count=12,
            risk_rating="LOW"
        )
        v3 = Vendor(
            name="Quantum Logistics Corp",
            tax_id="GSTIN07AABCQ9876K1",
            email="accounts@quantumlogistics.com",
            phone="+91 11 4567 8901",
            address="Okhla Industrial Area, New Delhi, India",
            average_invoice_amount=85000.00,
            historical_invoice_count=9,
            risk_rating="MEDIUM"
        )
        v4 = Vendor(
            name="Starlight Media Services",
            tax_id="GSTIN33AABCS5432M1",
            email="invoicing@starlightmedia.com",
            phone="+91 44 2345 6789",
            address="T. Nagar, Chennai, India",
            average_invoice_amount=40000.00,
            historical_invoice_count=15,
            risk_rating="LOW"
        )
        v5 = Vendor(
            name="Vertex Cloud Infra",
            tax_id="GSTIN36AABCV3321L1",
            email="billing@vertexcloud.io",
            phone="+91 40 6789 0123",
            address="HITEC City, Hyderabad, India",
            average_invoice_amount=45000.00,
            historical_invoice_count=24,
            risk_rating="LOW"
        )
        db.add_all([v1, v2, v3, v4, v5])
        db.commit()
        for v in [v1, v2, v3, v4, v5]:
            db.refresh(v)

        today = date.today()

        # 4. Seed Purchase Orders
        po1 = PurchaseOrder(
            po_number="PO-2026-101",
            vendor_id=v1.id,
            vendor_name=v1.name,
            po_date=today - timedelta(days=20),
            subtotal=127118.64,
            tax_amount=22881.36,
            total_amount=150000.00,
            currency="INR",
            status="APPROVED",
            line_items=json.dumps([
                {"description": "Enterprise Cloud Architecture Consulting", "quantity": 1, "unit_price": 100000.00, "total": 100000.00},
                {"description": "DevOps Pipeline Modernization", "quantity": 1, "unit_price": 50000.00, "total": 50000.00}
            ]),
            notes="Approved standard master services agreement."
        )

        po2 = PurchaseOrder(
            po_number="PO-2026-102",
            vendor_id=v2.id,
            vendor_name=v2.name,
            po_date=today - timedelta(days=18),
            subtotal=72033.90,
            tax_amount=12966.10,
            total_amount=85000.00,
            currency="INR",
            status="APPROVED",
            line_items=json.dumps([
                {"description": "UI/UX Design Sprint - Web App", "quantity": 1, "unit_price": 85000.00, "total": 85000.00}
            ]),
            notes="Design deliverables milestone 1."
        )

        po3 = PurchaseOrder(
            po_number="PO-2026-103",
            vendor_id=v3.id,
            vendor_name=v3.name,
            po_date=today - timedelta(days=15),
            subtotal=72033.90,
            tax_amount=12966.10,
            total_amount=85000.00,  # Note: PO is ₹85,000, but Invoice will bill ₹90,000
            currency="INR",
            status="APPROVED",
            line_items=json.dumps([
                {"description": "Inter-state Freight Logistics & Warehousing", "quantity": 1, "unit_price": 85000.00, "total": 85000.00}
            ]),
            notes="Approved freight rate cap at 85k."
        )

        po4 = PurchaseOrder(
            po_number="PO-2026-104",
            vendor_id=v4.id,
            vendor_name=v4.name,
            po_date=today - timedelta(days=10),
            subtotal=33898.31,
            tax_amount=6101.69,
            total_amount=40000.00,
            currency="INR",
            status="APPROVED",
            line_items=json.dumps([
                {"description": "Monthly Content Marketing & PR Distribution", "quantity": 1, "unit_price": 40000.00, "total": 40000.00}
            ]),
            notes="Standard monthly retainer."
        )

        po5 = PurchaseOrder(
            po_number="PO-2026-105",
            vendor_id=v5.id,
            vendor_name=v5.name,
            po_date=today - timedelta(days=5),
            subtotal=38135.59,
            tax_amount=6864.41,
            total_amount=45000.00,
            currency="INR",
            status="APPROVED",
            line_items=json.dumps([
                {"description": "Server Hosting & Database Cluster Infrastructure", "quantity": 1, "unit_price": 45000.00, "total": 45000.00}
            ]),
            notes="Monthly standard baseline tier."
        )

        db.add_all([po1, po2, po3, po4, po5])
        db.commit()
        for po in [po1, po2, po3, po4, po5]:
            db.refresh(po)

        # -------------------------------------------------------------
        # 5. Create Invoices for the 5 Demo Scenarios
        # -------------------------------------------------------------
        
        # Scenario 1: Perfect Match (₹1,50,000)
        inv1 = Invoice(
            invoice_number="INV-2026-001",
            vendor_id=v1.id,
            vendor_name=v1.name,
            po_id=po1.id,
            po_number=po1.po_number,
            invoice_date=today - timedelta(days=14),
            due_date=today + timedelta(days=16),
            subtotal=127118.64,
            tax_amount=22881.36,
            total_amount=150000.00,
            currency="INR",
            line_items=po1.line_items,
            raw_extracted_text=f"Apex Global Technologies Invoice INV-2026-001 PO: PO-2026-101 Total: INR 150000.00",
            file_name="sample_perfect_match.pdf",
            upload_status="PROCESSED"
        )

        # Scenario 2: Payment Mismatch (Invoice = ₹85,000, Payment = ₹80,000)
        inv2 = Invoice(
            invoice_number="INV-2026-002",
            vendor_id=v2.id,
            vendor_name=v2.name,
            po_id=po2.id,
            po_number=po2.po_number,
            invoice_date=today - timedelta(days=12),
            due_date=today + timedelta(days=18),
            subtotal=72033.90,
            tax_amount=12966.10,
            total_amount=85000.00,
            currency="INR",
            line_items=po2.line_items,
            raw_extracted_text=f"Nova Solutions Pvt Ltd Invoice INV-2026-002 PO: PO-2026-102 Total: INR 85000.00",
            file_name="sample_payment_mismatch.pdf",
            upload_status="PROCESSED"
        )

        # Scenario 3: PO Mismatch (Invoice = ₹90,000, PO = ₹85,000)
        inv3 = Invoice(
            invoice_number="INV-2026-003",
            vendor_id=v3.id,
            vendor_name=v3.name,
            po_id=po3.id,
            po_number=po3.po_number,
            invoice_date=today - timedelta(days=8),
            due_date=today + timedelta(days=22),
            subtotal=76271.19,
            tax_amount=13728.81,
            total_amount=90000.00, # Discrepancy: ₹5,000 more than PO
            currency="INR",
            line_items=json.dumps([
                {"description": "Inter-state Freight Logistics (Unapproved Surcharge)", "quantity": 1, "unit_price": 90000.00, "total": 90000.00}
            ]),
            raw_extracted_text=f"Quantum Logistics Corp Invoice INV-2026-003 PO: PO-2026-103 Total: INR 90000.00",
            file_name="sample_po_mismatch.pdf",
            upload_status="PROCESSED"
        )

        # Scenario 4: Original invoice for Duplicate Test
        inv4_orig = Invoice(
            invoice_number="INV-2026-004",
            vendor_id=v4.id,
            vendor_name=v4.name,
            po_id=po4.id,
            po_number=po4.po_number,
            invoice_date=today - timedelta(days=25),
            due_date=today + timedelta(days=5),
            subtotal=33898.31,
            tax_amount=6101.69,
            total_amount=40000.00,
            currency="INR",
            line_items=po4.line_items,
            raw_extracted_text=f"Starlight Media Services Invoice INV-2026-004 PO: PO-2026-104 Total: INR 40000.00",
            file_name="sample_duplicate_original.pdf",
            upload_status="PROCESSED"
        )

        # Scenario 4 (Duplicate Attempt): Identical invoice number submitted again
        inv4_dupe = Invoice(
            invoice_number="INV-2026-004",
            vendor_id=v4.id,
            vendor_name=v4.name,
            po_id=po4.id,
            po_number=po4.po_number,
            invoice_date=today - timedelta(days=2),
            due_date=today + timedelta(days=28),
            subtotal=33898.31,
            tax_amount=6101.69,
            total_amount=40000.00,
            currency="INR",
            line_items=po4.line_items,
            raw_extracted_text=f"Starlight Media Services Duplicate Invoice INV-2026-004 PO: PO-2026-104 Total: INR 40000.00",
            file_name="sample_duplicate_invoice.pdf",
            upload_status="PROCESSED"
        )

        # Scenario 5: Unusual Amount Anomaly (Invoice = ₹3,20,000 vs Vendor avg ₹45,000)
        inv5 = Invoice(
            invoice_number="INV-2026-005",
            vendor_id=v5.id,
            vendor_name=v5.name,
            po_id=po5.id,
            po_number=po5.po_number,
            invoice_date=today - timedelta(days=1),
            due_date=today + timedelta(days=29),
            subtotal=271186.44,
            tax_amount=48813.56,
            total_amount=320000.00, # Huge spike outlier
            currency="INR",
            line_items=json.dumps([
                {"description": "Special High-Performance GPU Cluster Allocation", "quantity": 1, "unit_price": 320000.00, "total": 320000.00}
            ]),
            raw_extracted_text=f"Vertex Cloud Infra Invoice INV-2026-005 PO: PO-2026-105 Total: INR 320000.00",
            file_name="sample_unusual_amount_anomaly.pdf",
            upload_status="PROCESSED"
        )

        db.add_all([inv1, inv2, inv3, inv4_orig, inv4_dupe, inv5])
        db.commit()
        for inv in [inv1, inv2, inv3, inv4_orig, inv4_dupe, inv5]:
            db.refresh(inv)

        # -------------------------------------------------------------
        # 6. Seed Banking Payments
        # -------------------------------------------------------------
        
        # Payment 1: Full Payment ₹1,50,000 for INV-2026-001
        pay1 = Payment(
            payment_reference="PAY-TXN-984210",
            invoice_id=inv1.id,
            invoice_number=inv1.invoice_number,
            po_id=po1.id,
            po_number=po1.po_number,
            vendor_id=v1.id,
            vendor_name=v1.name,
            payment_date=today - timedelta(days=10),
            amount_paid=150000.00,
            currency="INR",
            payment_method="NEFT",
            status="COMPLETED",
            notes="Automated vendor payout batch #441."
        )

        # Payment 2: Partial Payment ₹80,000 for INV-2026-002 (Shortfall ₹5,000)
        pay2 = Payment(
            payment_reference="PAY-TXN-984211",
            invoice_id=inv2.id,
            invoice_number=inv2.invoice_number,
            po_id=po2.id,
            po_number=po2.po_number,
            vendor_id=v2.id,
            vendor_name=v2.name,
            payment_date=today - timedelta(days=9),
            amount_paid=80000.00,
            currency="INR",
            payment_method="RTGS",
            status="COMPLETED",
            notes="Milestone partial disbursement."
        )

        # Payment 4: Paid earlier for original invoice 4
        pay4 = Payment(
            payment_reference="PAY-TXN-984212",
            invoice_id=inv4_orig.id,
            invoice_number=inv4_orig.invoice_number,
            po_id=po4.id,
            po_number=po4.po_number,
            vendor_id=v4.id,
            vendor_name=v4.name,
            payment_date=today - timedelta(days=20),
            amount_paid=40000.00,
            currency="INR",
            payment_method="BANK_TRANSFER",
            status="COMPLETED",
            notes="Original billing cleared."
        )

        db.add_all([pay1, pay2, pay4])
        db.commit()

        # -------------------------------------------------------------
        # 7. Run Reconciliation Pipeline on all Seed Invoices
        # -------------------------------------------------------------
        print("[RECON] Running Multi-Agent Reconciliation Engine on seed records...")
        for inv in [inv1, inv2, inv3, inv4_orig, inv4_dupe, inv5]:
            ReconciliationService.run_reconciliation(inv.id, db)

        print("[SUCCESS] Database seeding completed successfully with 5 core reconciliation demo scenarios!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
