import os
import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from backend.models.reconciliation_model import ReconciliationResult
from backend.utils.helpers import format_currency

class ReportService:
    """Service to generate professional, enterprise-grade PDF reconciliation audit reports."""

    @classmethod
    def generate_audit_report_pdf(cls, recon: ReconciliationResult) -> bytes:
        """Generates audit report PDF bytes for a given reconciliation result."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Define custom styles
        primary_color = colors.HexColor('#0f172a') # Deep Slate/Navy
        accent_blue = colors.HexColor('#2563eb')
        border_color = colors.HexColor('#e2e8f0')
        header_bg = colors.HexColor('#f8fafc')
        text_muted = colors.HexColor('#64748b')

        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=18,
            fontName='Helvetica-Bold',
            textColor=primary_color,
            leading=22
        )

        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=text_muted,
            leading=12
        )

        section_title = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=primary_color,
            spaceBefore=10,
            spaceAfter=6
        )

        meta_label = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=text_muted,
            leading=10
        )

        meta_val = ParagraphStyle(
            'MetaVal',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
            textColor=primary_color,
            leading=12
        )

        tbl_hdr = ParagraphStyle(
            'TableHdr',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=primary_color,
            leading=10
        )

        tbl_cell = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Helvetica',
            textColor=primary_color,
            leading=11
        )

        callout_text = ParagraphStyle(
            'CalloutText',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
            textColor=colors.HexColor('#1e293b'),
            leading=13
        )

        story = []

        invoice = recon.invoice
        po = recon.purchase_order
        payment = recon.payment
        inv_amt = float(invoice.total_amount) if invoice and invoice.total_amount is not None else 0.0
        po_amt = float(po.total_amount) if po and po.total_amount is not None else 0.0
        pay_amt = float(payment.amount_paid) if payment and payment.amount_paid is not None else 0.0
        po_diff = float(recon.amount_difference_po) if recon.amount_difference_po is not None else 0.0
        pay_diff = float(recon.amount_difference_payment) if recon.amount_difference_payment is not None else 0.0

        # Status badge color
        status_colors = {
            "MATCHED": colors.HexColor('#16a34a'),
            "REVIEW_REQUIRED": colors.HexColor('#d97706'),
            "HIGH_RISK": colors.HexColor('#dc2626'),
            "REJECT": colors.HexColor('#b91c1c')
        }
        badge_color = status_colors.get(recon.status, primary_color)

        # -------------------------------------------------------------
        # 1. Header Banner
        # -------------------------------------------------------------
        header_data = [
            [
                Paragraph("<b>INVOICE RECONCILIATION AUDIT REPORT</b>", title_style),
                Paragraph(f"<b>STATUS: {recon.status}</b>", ParagraphStyle('StatusBadge', parent=meta_label, fontSize=11, textColor=badge_color, alignment=2))
            ],
            [
                Paragraph("Enterprise Multi-Agent Autonomous Finance Platform | Confidential Audit Document", subtitle_style),
                Paragraph(f"Report Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", ParagraphStyle('RptDate', parent=subtitle_style, alignment=2))
            ]
        ]
        t_head = Table(header_data, colWidths=[360, 180])
        t_head.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(t_head)
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1.5, color=accent_blue, spaceAfter=10))

        # -------------------------------------------------------------
        # 2. Executive 3-Way Match Summary Card
        # -------------------------------------------------------------
        story.append(Paragraph("1. Executive Three-Way Matching Summary", section_title))
        summary_grid = [
            [
                Paragraph("INVOICE LIABILITY", meta_label),
                Paragraph("AUTHORIZED PO", meta_label),
                Paragraph("BANKING SETTLEMENT", meta_label),
                Paragraph("DECISION & RISK", meta_label)
            ],
            [
                Paragraph(f"<b>{format_currency(inv_amt, 'Rs. ')}</b><br/>Ref: {invoice.invoice_number if invoice else 'N/A'}", meta_val),
                Paragraph(f"<b>{format_currency(po_amt, 'Rs. ')}</b><br/>PO: {po.po_number if po else (invoice.po_number if invoice else 'N/A')}<br/>Status: <b>{recon.po_match_status}</b>", meta_val),
                Paragraph(f"<b>{format_currency(pay_amt, 'Rs. ')}</b><br/>Ref: {payment.payment_reference if payment else 'N/A'}<br/>Status: <b>{recon.payment_match_status}</b>", meta_val),
                Paragraph(f"Decision: <b>{recon.status}</b><br/>Risk Score: <b>{recon.risk_score}/100</b> ({recon.risk_level})<br/>Confidence: <b>{float(recon.confidence_score):.1f}%</b>", meta_val)
            ]
        ]
        t_sum = Table(summary_grid, colWidths=[135, 135, 135, 135])
        t_sum.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ffffff')),
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t_sum)
        story.append(Spacer(1, 10))

        # -------------------------------------------------------------
        # 3. Document Details (Invoice vs PO vs Payment)
        # -------------------------------------------------------------
        story.append(Paragraph("2. Financial Document & Verification Breakdown", section_title))
        details_data = [
            [Paragraph("Document Entity", tbl_hdr), Paragraph("Key Parameters", tbl_hdr), Paragraph("Audit & Ledger State", tbl_hdr)],
            [
                Paragraph("<b>Invoice Details</b>", tbl_cell),
                Paragraph(f"Vendor: <b>{invoice.vendor_name if invoice else 'N/A'}</b><br/>Invoice Date: {invoice.invoice_date if invoice else 'N/A'}<br/>Due Date: {invoice.due_date if invoice else 'N/A'}", tbl_cell),
                Paragraph(f"Subtotal: {format_currency(invoice.subtotal, 'Rs. ') if invoice else 'N/A'}<br/>Tax (18%): {format_currency(invoice.tax_amount, 'Rs. ') if invoice else 'N/A'}<br/><b>Total: {format_currency(inv_amt, 'Rs. ')}</b>", tbl_cell)
            ],
            [
                Paragraph("<b>Purchase Order</b>", tbl_cell),
                Paragraph(f"PO Ref: <b>{po.po_number if po else (invoice.po_number if invoice else 'N/A')}</b><br/>Vendor on PO: {po.vendor_name if po else 'N/A'}<br/>Issue Date: {po.po_date if po else 'N/A'}", tbl_cell),
                Paragraph(f"Authorized Cap: {format_currency(po_amt, 'Rs. ')}<br/>Variance: <b>{format_currency(po_diff, 'Rs. ')}</b><br/>Match Result: <b>{recon.po_match_status}</b>", tbl_cell)
            ],
            [
                Paragraph("<b>Banking Ledger</b>", tbl_cell),
                Paragraph(f"Payment Ref: <b>{payment.payment_reference if payment else 'N/A'}</b><br/>Payment Date: {payment.payment_date if payment else 'N/A'}<br/>Method: {payment.payment_method if payment else 'N/A'}", tbl_cell),
                Paragraph(f"Disbursed Amount: {format_currency(pay_amt, 'Rs. ')}<br/>Difference: <b>{format_currency(pay_diff, 'Rs. ')}</b><br/>Ledger State: <b>{recon.payment_match_status}</b>", tbl_cell)
            ]
        ]
        t_det = Table(details_data, colWidths=[110, 215, 215])
        t_det.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t_det)
        story.append(Spacer(1, 10))

        # -------------------------------------------------------------
        # 4. Explainable AI Risk Factor Breakdown
        # -------------------------------------------------------------
        story.append(Paragraph("3. Explainable Risk Scoring & Anomaly Factors", section_title))
        
        # Parse factors
        risk_breakdown_raw = recon.get_risk_breakdown()
        factors_to_render = []
        if isinstance(risk_breakdown_raw, dict):
            factors_to_render = risk_breakdown_raw.get("all_vector_checks") or risk_breakdown_raw.get("factors", [])
        elif isinstance(risk_breakdown_raw, list):
            factors_to_render = risk_breakdown_raw

        if not factors_to_render:
            factors_to_render = [
                {"factor": "Purchase Order Variance", "points": 35 if recon.po_match_status == "MISMATCH" else 0, "severity": "HIGH" if recon.po_match_status == "MISMATCH" else "LOW", "status": "FAILED" if recon.po_match_status == "MISMATCH" else "PASSED", "description": f"PO Status: {recon.po_match_status}"},
                {"factor": "Payment Mismatch", "points": 25 if recon.payment_match_status in ["PARTIAL_PAYMENT", "OVERPAYMENT"] else 0, "severity": "MEDIUM" if recon.payment_match_status in ["PARTIAL_PAYMENT", "OVERPAYMENT"] else "LOW", "status": "WARNING" if recon.payment_match_status in ["PARTIAL_PAYMENT", "OVERPAYMENT"] else "PASSED", "description": f"Payment: {recon.payment_match_status}"},
                {"factor": "Duplicate Invoice Check", "points": 45 if recon.duplicate_status == "DUPLICATE_FOUND" else 0, "severity": "CRITICAL" if recon.duplicate_status == "DUPLICATE_FOUND" else "LOW", "status": "FAILED" if recon.duplicate_status == "DUPLICATE_FOUND" else "PASSED", "description": "Duplicate invoice test."},
                {"factor": "Statistical Amount Anomaly", "points": 45 if recon.anomaly_status == "ANOMALY_DETECTED" else 0, "severity": "HIGH" if recon.anomaly_status == "ANOMALY_DETECTED" else "LOW", "status": "FAILED" if recon.anomaly_status == "ANOMALY_DETECTED" else "PASSED", "description": "Vendor amount anomaly test."}
            ]

        risk_rows = [
            [Paragraph("Risk Vector", tbl_hdr), Paragraph("Points", tbl_hdr), Paragraph("Status", tbl_hdr), Paragraph("Evaluation & Description", tbl_hdr)]
        ]
        for factor in factors_to_render:
            pts = factor.get("points", 0)
            pts_str = f"+{pts}" if pts > 0 else "0"
            risk_rows.append([
                Paragraph(f"<b>{factor.get('factor', 'Risk Factor')}</b>", tbl_cell),
                Paragraph(f"<b>{pts_str}</b>", ParagraphStyle('Pts', parent=tbl_cell, fontName='Helvetica-Bold', textColor=colors.HexColor('#dc2626') if pts > 0 else colors.HexColor('#16a34a'))),
                Paragraph(factor.get('status', 'EVALUATED'), tbl_cell),
                Paragraph(factor.get('description', ''), tbl_cell)
            ])

        t_risk = Table(risk_rows, colWidths=[130, 45, 65, 300])
        t_risk.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t_risk)
        story.append(Spacer(1, 10))

        # -------------------------------------------------------------
        # 5. AI Reasoning & Concrete Recommendation Box
        # -------------------------------------------------------------
        story.append(KeepTogether([
            Paragraph("4. AI Synthesis & Remediation Recommendation", section_title),
            Table([
                [Paragraph("<b>AI Diagnosis:</b>", meta_label)],
                [Paragraph(recon.ai_explanation or "The multi-agent system evaluated invoice, PO, and payment records without finding discrepancies.", callout_text)],
                [Spacer(1, 4)],
                [Paragraph("<b>Recommended Next Action:</b>", meta_label)],
                [Paragraph(recon.ai_recommendation or "No remedial action required. Invoice is fully authorized for standard reconciliation closure.", callout_text)]
            ], colWidths=[540], style=[
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eff6ff')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#93c5fd')),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]),
            Spacer(1, 10)
        ]))

        # -------------------------------------------------------------
        # 6. Human-in-the-Loop Governance Sign-Off Box
        # -------------------------------------------------------------
        gov_status = recon.human_action or "PENDING"
        gov_date = recon.reviewed_at.strftime('%Y-%m-%d %H:%M:%S UTC') if recon.reviewed_at else "Pending human reviewer action"
        gov_notes = recon.reviewer_notes or "No notes submitted."

        gov_table = Table([
            [Paragraph("<b>5. Human-in-the-Loop Governance & Audit Sign-Off</b>", section_title), Paragraph(f"<b>ACTION: {gov_status}</b>", ParagraphStyle('GovAct', parent=meta_label, fontSize=10, textColor=badge_color, alignment=2))],
            [
                Paragraph(f"<b>Sign-off State:</b> {gov_status}<br/><b>Audit Timestamp:</b> {gov_date}", tbl_cell),
                Paragraph(f"<b>Reviewer Notes:</b><br/>{gov_notes}", tbl_cell)
            ]
        ], colWidths=[270, 270])
        gov_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), header_bg),
            ('BOX', (0, 0), (-1, -1), 0.5, border_color),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(gov_table)

        # Build PDF document
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
