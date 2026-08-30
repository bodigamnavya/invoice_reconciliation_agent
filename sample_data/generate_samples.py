import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVOICES_DIR = os.path.join(BASE_DIR, "invoices")
POS_DIR = os.path.join(BASE_DIR, "purchase_orders")
PAYMENTS_DIR = os.path.join(BASE_DIR, "payments")

os.makedirs(INVOICES_DIR, exist_ok=True)
os.makedirs(POS_DIR, exist_ok=True)
os.makedirs(PAYMENTS_DIR, exist_ok=True)

def create_invoice_pdf(filename, invoice_num, vendor_name, vendor_addr, po_num, inv_date, due_date, items, subtotal, tax, total):
    file_path = os.path.join(INVOICES_DIR, filename)
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=6
    )
    
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#475569'),
        leading=14
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=colors.white
    )
    
    story = []
    
    # Header
    story.append(Paragraph("TAX INVOICE", title_style))
    story.append(Paragraph(f"<b>{vendor_name}</b><br/>{vendor_addr}", meta_style))
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=15))
    
    # Metadata grid
    meta_data = [
        [
            Paragraph(f"<b>Invoice Number:</b> {invoice_num}", meta_style),
            Paragraph(f"<b>Invoice Date:</b> {inv_date}", meta_style)
        ],
        [
            Paragraph(f"<b>Purchase Order:</b> {po_num}", meta_style),
            Paragraph(f"<b>Payment Due:</b> {due_date}", meta_style)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[270, 260])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))
    
    # Line Items Table
    table_data = [[
        Paragraph("Item Description", table_header_style),
        Paragraph("Qty", table_header_style),
        Paragraph("Unit Price (INR)", table_header_style),
        Paragraph("Total (INR)", table_header_style)
    ]]
    
    for item in items:
        table_data.append([
            Paragraph(item["description"], meta_style),
            Paragraph(str(item["quantity"]), meta_style),
            Paragraph(f"Rs. {item['unit_price']:,.2f}", meta_style),
            Paragraph(f"Rs. {item['total']:,.2f}", meta_style)
        ])
    
    t_items = Table(table_data, colWidths=[270, 50, 100, 110])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 15))
    
    # Summary Table
    summary_data = [
        [Paragraph("<b>Subtotal:</b>", meta_style), Paragraph(f"Rs. {subtotal:,.2f}", meta_style)],
        [Paragraph("<b>GST / Tax (18%):</b>", meta_style), Paragraph(f"Rs. {tax:,.2f}", meta_style)],
        [Paragraph("<b>Total Amount Due:</b>", ParagraphStyle('Tot', parent=meta_style, fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#0f172a'))),
         Paragraph(f"<b>Rs. {total:,.2f}</b>", ParagraphStyle('TotVal', parent=meta_style, fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#2563eb')))]
    ]
    t_summary = Table(summary_data, colWidths=[420, 110])
    t_summary.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_summary)
    
    # Footer Notes
    story.append(Spacer(1, 30))
    story.append(Paragraph("<b>Payment Terms:</b> Net 30 Days. Please transfer to designated banking account quoting invoice number.", meta_style))
    
    doc.build(story)
    print(f"Generated sample PDF: {file_path}")

def generate_all_samples():
    print("[SAMPLES] Generating demo invoice PDF documents...")

    # 1. Perfect Match Invoice
    create_invoice_pdf(
        "1_perfect_match_INV-2026-001.pdf",
        "INV-2026-001",
        "Apex Global Technologies",
        "Tech Park Phase 2, Bangalore, India | GSTIN29AAACA0001Z1",
        "PO-2026-101",
        "2026-08-16",
        "2026-09-15",
        [
            {"description": "Enterprise Cloud Architecture Consulting", "quantity": 1, "unit_price": 100000.00, "total": 100000.00},
            {"description": "DevOps Pipeline Modernization", "quantity": 1, "unit_price": 50000.00, "total": 50000.00}
        ],
        127118.64,
        22881.36,
        150000.00
    )

    # 2. Payment Mismatch Invoice
    create_invoice_pdf(
        "2_payment_mismatch_INV-2026-002.pdf",
        "INV-2026-002",
        "Nova Solutions Pvt Ltd",
        "Nariman Point, Mumbai, India | GSTIN27AABCN1234F1",
        "PO-2026-102",
        "2026-08-18",
        "2026-09-17",
        [
            {"description": "UI/UX Design Sprint - Web App", "quantity": 1, "unit_price": 85000.00, "total": 85000.00}
        ],
        72033.90,
        12966.10,
        85000.00
    )

    # 3. PO Mismatch Invoice
    create_invoice_pdf(
        "3_po_mismatch_INV-2026-003.pdf",
        "INV-2026-003",
        "Quantum Logistics Corp",
        "Okhla Industrial Area, New Delhi, India | GSTIN07AABCQ9876K1",
        "PO-2026-103",
        "2026-08-22",
        "2026-09-21",
        [
            {"description": "Inter-state Freight Logistics & Unapproved Surcharge", "quantity": 1, "unit_price": 90000.00, "total": 90000.00}
        ],
        76271.19,
        13728.81,
        90000.00
    )

    # 4. Duplicate Invoice
    create_invoice_pdf(
        "4_duplicate_invoice_INV-2026-004.pdf",
        "INV-2026-004",
        "Starlight Media Services",
        "T. Nagar, Chennai, India | GSTIN33AABCS5432M1",
        "PO-2026-104",
        "2026-08-28",
        "2026-09-27",
        [
            {"description": "Monthly Content Marketing & PR Distribution", "quantity": 1, "unit_price": 40000.00, "total": 40000.00}
        ],
        33898.31,
        6101.69,
        40000.00
    )

    # 5. Unusual Amount Outlier Anomaly Invoice
    create_invoice_pdf(
        "5_anomaly_unusual_amount_INV-2026-005.pdf",
        "INV-2026-005",
        "Vertex Cloud Infra",
        "HITEC City, Hyderabad, India | GSTIN36AABCV3321L1",
        "PO-2026-105",
        "2026-08-29",
        "2026-09-28",
        [
            {"description": "Special High-Performance GPU Cluster Allocation", "quantity": 1, "unit_price": 320000.00, "total": 320000.00}
        ],
        271186.44,
        48813.56,
        320000.00
    )

    # JSON metadata files for purchase orders and payments
    with open(os.path.join(POS_DIR, "demo_purchase_orders.json"), "w") as f:
        json.dump([
            {"po_number": "PO-2026-101", "vendor": "Apex Global Technologies", "amount": 150000.00, "status": "APPROVED"},
            {"po_number": "PO-2026-102", "vendor": "Nova Solutions Pvt Ltd", "amount": 85000.00, "status": "APPROVED"},
            {"po_number": "PO-2026-103", "vendor": "Quantum Logistics Corp", "amount": 85000.00, "status": "APPROVED"},
            {"po_number": "PO-2026-104", "vendor": "Starlight Media Services", "amount": 40000.00, "status": "APPROVED"},
            {"po_number": "PO-2026-105", "vendor": "Vertex Cloud Infra", "amount": 45000.00, "status": "APPROVED"}
        ], f, indent=2)

    with open(os.path.join(PAYMENTS_DIR, "demo_banking_payments.json"), "w") as f:
        json.dump([
            {"ref": "PAY-TXN-984210", "invoice": "INV-2026-001", "amount": 150000.00, "status": "COMPLETED"},
            {"ref": "PAY-TXN-984211", "invoice": "INV-2026-002", "amount": 80000.00, "status": "COMPLETED"},
            {"ref": "PAY-TXN-984212", "invoice": "INV-2026-004", "amount": 40000.00, "status": "COMPLETED"}
        ], f, indent=2)

    print("[SUCCESS] All sample data and PDF invoices generated!")

if __name__ == "__main__":
    generate_all_samples()
