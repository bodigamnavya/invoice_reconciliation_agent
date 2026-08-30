/**
 * RECON AI - RECONCILIATION INSPECTOR CONTROLLER (reconciliation.js)
 * Implements Feature 1 (Explainable AI Audit Trail) & Feature 3 (Audit Report Generator)
 */

let currentInvoiceId = null;
let currentVendorId = null;

document.addEventListener("DOMContentLoaded", () => {
  Auth.requireAuth();

  const urlParams = new URLSearchParams(window.location.search);
  currentInvoiceId = urlParams.get("id");

  if (!currentInvoiceId) {
    showToast("No invoice ID provided. Redirecting to dashboard...", "warning");
    setTimeout(() => window.location.href = "dashboard.html", 1500);
    return;
  }

  loadReconciliationData(currentInvoiceId);
  setupActionButtons();
  setupReportButtons();
});

async function loadReconciliationData(invoiceId) {
  try {
    const res = await fetch(`${CONFIG.API_BASE}/reconciliation/${invoiceId}`, {
      headers: {
        "Authorization": `Bearer ${Auth.getToken()}`
      }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || "Failed to load reconciliation record.");

    renderReconciliationUI(data.reconciliation);
  } catch (err) {
    showToast(err.message, "error");
  }
}

function renderReconciliationUI(recon) {
  if (!recon) return;

  const inv = recon.invoice || {};
  const po = recon.purchase_order || {};
  const pay = recon.payment || {};
  const audit = recon.audit_trail || {};

  currentVendorId = inv.vendor_id || 1;

  // 1. Header Details
  document.getElementById("recon-invoice-num").textContent = inv.invoice_number || `INV-${recon.invoice_id}`;
  
  const vendorEl = document.getElementById("recon-vendor-name");
  if (vendorEl) {
    vendorEl.innerHTML = `<span>${inv.vendor_name || "Apex Global Technologies"}</span> <i class="bi bi-box-arrow-up-right" style="font-size: 0.95rem; color: #38bdf8;"></i>`;
    vendorEl.onclick = () => {
      window.location.href = `vendor.html?id=${currentVendorId}`;
    };
  }

  const vendorLinkTop = document.getElementById("link-vendor-profile");
  if (vendorLinkTop) {
    vendorLinkTop.href = `vendor.html?id=${currentVendorId}`;
  }

  document.getElementById("recon-status-badge").innerHTML = getStatusBadge(recon.status);
  document.getElementById("recon-risk-badge").innerHTML = getRiskBadge(recon.risk_level);
  document.getElementById("recon-risk-score-val").textContent = `${recon.risk_score}/100`;

  // Human Action status badge in header
  const actionBadge = document.getElementById("recon-human-action-badge");
  if (actionBadge) {
    actionBadge.textContent = recon.human_action || "PENDING";
    actionBadge.className = `badge ${recon.human_action === 'APPROVED' ? 'bg-success' : recon.human_action === 'REJECTED' ? 'bg-danger' : recon.human_action === 'REVIEWED' ? 'bg-warning text-dark' : 'bg-secondary'}`;
  }

  // 2. AI Reasoning Box
  document.getElementById("ai-final-decision-text").textContent = (recon.status || "").replace("_", " ");
  document.getElementById("ai-reason-text").textContent = recon.ai_reason || "Reconciliation audit analysis complete.";
  document.getElementById("ai-explanation-text").textContent = recon.ai_explanation || "No explanation recorded.";
  document.getElementById("ai-recommendation-text").textContent = recon.ai_recommendation || "Review line items.";
  document.getElementById("ai-confidence-score").textContent = `${recon.confidence_score || 95}%`;

  // 3. Feature 1: Explainable AI Audit Trail Discrepancy Matrix
  const varSummary = audit.variance_summary || {};
  const invTotal = inv.total_amount || 0;
  const poTotal = po.total_amount || varSummary.po_amount || 0;
  const poDiff = recon.amount_difference_po || varSummary.po_variance || 0;
  const poPct = varSummary.po_variance_percent || (poTotal > 0 ? ((Math.abs(poDiff) / poTotal) * 100).toFixed(2) : "0.00");
  const payTotal = pay.amount_paid || varSummary.payment_amount || 0;
  const payDiff = recon.amount_difference_payment || varSummary.payment_variance || 0;

  document.getElementById("audit-trail-risk-tag").textContent = `Risk: ${recon.risk_score}/100 (${recon.risk_level})`;
  document.getElementById("audit-inv-amt").textContent = formatCurrency(invTotal);
  document.getElementById("audit-po-amt").textContent = formatCurrency(poTotal);
  document.getElementById("audit-po-diff").textContent = (poDiff > 0 ? "+" : "") + formatCurrency(poDiff);
  document.getElementById("audit-po-pct").textContent = `${poPct}%`;
  document.getElementById("audit-pay-amt").textContent = formatCurrency(payTotal);
  document.getElementById("audit-pay-diff").textContent = (payDiff < 0 ? "-" : "+") + formatCurrency(Math.abs(payDiff));

  // Risk Factors Breakdown Table
  const auditFactorsTbody = document.getElementById("audit-factors-table-body");
  const vectorChecks = audit.all_vector_checks || recon.risk_breakdown || [];

  if (auditFactorsTbody) {
    if (vectorChecks.length === 0) {
      auditFactorsTbody.innerHTML = `<tr><td colspan="4" class="text-center text-success py-3"><i class="bi bi-shield-check"></i> All compliance checks passed without penalty points.</td></tr>`;
    } else {
      auditFactorsTbody.innerHTML = vectorChecks.map(f => {
        const pts = f.points !== undefined ? f.points : (f.weight || 0);
        const ptsBadge = pts > 0 
          ? `<span class="badge bg-danger font-semibold">+${pts} pts</span>`
          : `<span class="badge bg-success font-semibold">0 pts</span>`;
        const statusBadge = f.status === 'FAILED'
          ? `<span class="badge bg-danger text-white">FAILED</span>`
          : f.status === 'WARNING'
          ? `<span class="badge bg-warning text-dark">WARNING</span>`
          : `<span class="badge bg-success text-white">PASSED</span>`;

        return `
          <tr>
            <td><strong>${f.factor}</strong></td>
            <td>${ptsBadge}</td>
            <td>${statusBadge}</td>
            <td style="color: #cbd5e1; font-size: 0.9rem;">${f.description}</td>
          </tr>
        `;
      }).join("");
    }
  }

  // Audit Timeline Events
  const timelineContainer = document.getElementById("audit-timeline-container");
  const timelineEvents = audit.timeline || [];
  if (timelineContainer && timelineEvents.length > 0) {
    timelineContainer.innerHTML = timelineEvents.map(evt => `
      <div style="display: flex; gap: 14px; align-items: flex-start; padding: 10px 14px; background: #0f172a; border-radius: var(--radius-sm); border-left: 3px solid ${evt.status === 'COMPLETED' ? '#22c55e' : evt.status === 'FLAGGED' ? '#f59e0b' : '#64748b'};">
        <div style="color: ${evt.status === 'COMPLETED' ? '#22c55e' : evt.status === 'FLAGGED' ? '#f59e0b' : '#94a3b8'}; font-size: 1.1rem; margin-top: 1px;">
          <i class="bi ${evt.status === 'COMPLETED' ? 'bi-check-circle-fill' : evt.status === 'FLAGGED' ? 'bi-exclamation-circle-fill' : 'bi-circle'}"></i>
        </div>
        <div style="flex: 1;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong style="color: #ffffff; font-size: 0.9rem;">${evt.name}</strong>
            <span style="font-size: 0.75rem; color: #94a3b8;" class="mono">${evt.timestamp || 'Pending'}</span>
          </div>
          <div style="font-size: 0.83rem; color: #94a3b8; margin-top: 2px;">${evt.details}</div>
        </div>
      </div>
    `).join("");
  }

  // 4. Card 1: Invoice Details
  document.getElementById("inv-total").textContent = formatCurrency(inv.total_amount);
  document.getElementById("inv-subtotal").textContent = formatCurrency(inv.subtotal);
  document.getElementById("inv-tax").textContent = formatCurrency(inv.tax_amount);
  document.getElementById("inv-date").textContent = formatDate(inv.invoice_date);
  document.getElementById("inv-due-date").textContent = formatDate(inv.due_date);
  document.getElementById("inv-quoted-po").textContent = inv.po_number || "None Listed";

  // 5. Card 2: Purchase Order
  const poCard = document.getElementById("po-card");
  if (po.id || po.po_number) {
    document.getElementById("po-number-val").textContent = po.po_number || inv.po_number;
    document.getElementById("po-total-val").textContent = formatCurrency(po.total_amount);
    document.getElementById("po-date-val").textContent = formatDate(po.po_date);
    document.getElementById("po-match-status-val").textContent = recon.po_match_status;
    document.getElementById("po-diff-val").textContent = formatCurrency(Math.abs(recon.amount_difference_po));
    
    if (recon.po_match_status === "MISMATCH") {
      poCard.classList.add("highlight-diff");
    }
  } else {
    document.getElementById("po-number-val").textContent = "Not Found";
    document.getElementById("po-total-val").textContent = "₹0.00";
    document.getElementById("po-date-val").textContent = "N/A";
    document.getElementById("po-match-status-val").textContent = "NOT_FOUND";
    document.getElementById("po-diff-val").textContent = "N/A";
  }

  // 6. Card 3: Payment Ledger
  const payCard = document.getElementById("payment-card");
  if (pay.id || pay.payment_reference) {
    document.getElementById("pay-ref-val").textContent = pay.payment_reference;
    document.getElementById("pay-amount-val").textContent = formatCurrency(pay.amount_paid);
    document.getElementById("pay-date-val").textContent = formatDate(pay.payment_date);
    document.getElementById("pay-method-val").textContent = pay.payment_method || "Direct Bank Transfer";
    document.getElementById("pay-match-status-val").textContent = (recon.payment_match_status || "").replace("_", " ");
    document.getElementById("pay-diff-val").textContent = formatCurrency(Math.abs(recon.amount_difference_payment));

    if (recon.payment_match_status === "PARTIAL_PAYMENT" || recon.payment_match_status === "OVERPAYMENT") {
      payCard.classList.add("highlight-diff");
    }
  } else {
    document.getElementById("pay-ref-val").textContent = "No Payment Found";
    document.getElementById("pay-amount-val").textContent = "₹0.00";
    document.getElementById("pay-date-val").textContent = "N/A";
    document.getElementById("pay-method-val").textContent = "N/A";
    document.getElementById("pay-match-status-val").textContent = "UNPAID";
    document.getElementById("pay-diff-val").textContent = formatCurrency(inv.total_amount);
  }

  // 7. Line Items Table
  const itemsTbody = document.getElementById("line-items-body");
  const lineItems = inv.line_items || [];
  if (itemsTbody) {
    if (lineItems.length === 0) {
      itemsTbody.innerHTML = `<tr><td colspan="5" class="text-center py-3 text-muted">No itemized line details extracted.</td></tr>`;
    } else {
      itemsTbody.innerHTML = lineItems.map((item, idx) => `
        <tr>
          <td>${idx + 1}</td>
          <td><strong>${item.description || 'Service/Item'}</strong></td>
          <td>${item.quantity || 1}</td>
          <td>${formatCurrency(item.unit_price || 0)}</td>
          <td class="font-semibold" style="color: #38bdf8;">${formatCurrency(item.total || item.unit_price || 0)}</td>
        </tr>
      `).join("");
    }
  }
}

function setupReportButtons() {
  const btnTop = document.getElementById("btn-generate-report");
  const btnBottom = document.getElementById("btn-generate-report-bottom");

  const triggerDownload = async () => {
    try {
      showToast("Generating audit report PDF...", "info");
      const res = await fetch(`${CONFIG.API_BASE}/reconciliation/${currentInvoiceId}/report`, {
        headers: {
          "Authorization": `Bearer ${Auth.getToken()}`
        }
      });
      if (!res.ok) throw new Error("Failed to generate PDF report from backend.");

      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `reconciliation_audit_report_${currentInvoiceId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);
      showToast("Audit Report PDF downloaded successfully!", "success");
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  if (btnTop) btnTop.addEventListener("click", triggerDownload);
  if (btnBottom) btnBottom.addEventListener("click", triggerDownload);
}

function setupActionButtons() {
  const btnApprove = document.getElementById("btn-approve");
  const btnReview = document.getElementById("btn-review");
  const btnReject = document.getElementById("btn-reject");

  if (btnApprove) {
    btnApprove.addEventListener("click", () => handleHumanAction("approve", "Approved by finance officer."));
  }
  if (btnReview) {
    btnReview.addEventListener("click", () => handleHumanAction("review", "Flagged for manual audit review."));
  }
  if (btnReject) {
    btnReject.addEventListener("click", () => handleHumanAction("reject", "Rejected due to validation failure."));
  }
}

async function handleHumanAction(actionType, defaultNotes) {
  const notes = prompt(`Enter optional review notes for marking as ${actionType.toUpperCase()}:`, defaultNotes);
  if (notes === null) return; // Cancelled

  try {
    const res = await fetch(`${CONFIG.API_BASE}/reconciliation/${currentInvoiceId}/${actionType}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${Auth.getToken()}`
      },
      body: JSON.stringify({ notes })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || "Action failed.");

    showToast(`Invoice marked as ${actionType.toUpperCase()}!`, "success");
    renderReconciliationUI(data.reconciliation);
  } catch (err) {
    showToast(err.message, "error");
  }
}
