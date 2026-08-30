/**
 * RECON AI - AUDIT HISTORY & SEARCH CONTROLLER (history.js)
 * Implements History Search, Direct PDF Report Download, and Vendor Profile Quick Access
 */

let allHistory = [];

document.addEventListener("DOMContentLoaded", () => {
  Auth.requireAuth();
  loadHistoryData();
  setupFilterEvents();
});

async function loadHistoryData() {
  const statusFilter = document.getElementById("filter-status") ? document.getElementById("filter-status").value : "ALL";
  const riskFilter = document.getElementById("filter-risk") ? document.getElementById("filter-risk").value : "ALL";
  const search = document.getElementById("search-input") ? document.getElementById("search-input").value.trim() : "";

  const queryParams = new URLSearchParams();
  if (statusFilter !== "ALL") queryParams.append("status", statusFilter);
  if (riskFilter !== "ALL") queryParams.append("risk_level", riskFilter);
  if (search) queryParams.append("search", search);

  try {
    const res = await fetch(`${CONFIG.API_BASE}/history?${queryParams.toString()}`, {
      headers: {
        "Authorization": `Bearer ${Auth.getToken()}`
      }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || "Failed to load reconciliation history.");

    allHistory = data.history || [];
    renderHistoryTable(allHistory);
  } catch (err) {
    showToast(err.message, "error");
  }
}

function setupFilterEvents() {
  const searchInput = document.getElementById("search-input");
  const filterStatus = document.getElementById("filter-status");
  const filterRisk = document.getElementById("filter-risk");
  const btnExport = document.getElementById("btn-export-csv");

  if (searchInput) searchInput.addEventListener("input", debounce(loadHistoryData, 300));
  if (filterStatus) filterStatus.addEventListener("change", loadHistoryData);
  if (filterRisk) filterRisk.addEventListener("change", loadHistoryData);
  if (btnExport) btnExport.addEventListener("click", exportToCSV);
}

function renderHistoryTable(records) {
  const tbody = document.getElementById("history-table-body");
  const countEl = document.getElementById("history-count");
  if (countEl) countEl.textContent = `${records.length} records found`;

  if (!tbody) return;

  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center py-5 text-muted">No reconciliation records match your query.</td></tr>`;
    return;
  }

  tbody.innerHTML = records.map(item => {
    const inv = item.invoice || {};
    const invoiceNum = inv.invoice_number || `INV-${item.invoice_id}`;
    const vendorName = inv.vendor_name || "Unknown";
    const vendorId = inv.vendor_id || 1;
    const amount = formatCurrency(inv.total_amount || 0);
    const dateStr = formatDate(inv.invoice_date || item.created_at);
    const statusBadge = getStatusBadge(item.status);
    const riskBadge = getRiskBadge(item.risk_level);
    const humanAction = item.human_action || "PENDING";

    return `
      <tr>
        <td class="mono font-semibold" style="color: #38bdf8;">${invoiceNum}</td>
        <td>
          <a href="vendor.html?id=${vendorId}" style="color: #ffffff; text-decoration: none; font-weight: 500;" title="View Vendor Profile">
            ${vendorName} <i class="bi bi-box-arrow-up-right small text-muted"></i>
          </a>
        </td>
        <td class="mono">${inv.po_number || '<span class="text-muted">None</span>'}</td>
        <td class="font-semibold">${amount}</td>
        <td>${dateStr}</td>
        <td>${statusBadge}</td>
        <td>${riskBadge} <span class="small text-muted font-bold">(${item.risk_score})</span></td>
        <td>
          <span class="badge ${humanAction === 'APPROVED' ? 'bg-success' : humanAction === 'REJECTED' ? 'bg-danger' : humanAction === 'REVIEWED' ? 'bg-warning text-dark' : 'bg-secondary'}">
            ${humanAction}
          </span>
        </td>
        <td class="text-end">
          <div style="display: flex; gap: 6px; justify-content: flex-end;">
            <a href="reconciliation.html?id=${item.invoice_id}" class="btn-recon btn-recon-primary btn-sm" title="Inspect 3-Way Reconciliation">
              <i class="bi bi-eye"></i>
            </a>
            <a href="vendor.html?id=${vendorId}" class="btn-recon btn-recon-outline btn-sm" title="Vendor Risk Profile">
              <i class="bi bi-building"></i>
            </a>
            <button onclick="downloadAuditReport(${item.invoice_id}, '${invoiceNum}')" class="btn-recon btn-recon-outline btn-sm" title="Download PDF Report">
              <i class="bi bi-file-earmark-pdf"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

async function downloadAuditReport(invoiceId, invoiceNum) {
  try {
    showToast(`Generating audit report for ${invoiceNum}...`, "info");
    const res = await fetch(`${CONFIG.API_BASE}/reconciliation/${invoiceId}/report`, {
      headers: {
        "Authorization": `Bearer ${Auth.getToken()}`
      }
    });
    if (!res.ok) throw new Error("Failed to download audit report.");

    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = `reconciliation_audit_report_${invoiceNum}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);
    showToast(`Report downloaded for ${invoiceNum}`, "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

function exportToCSV() {
  if (!allHistory || allHistory.length === 0) {
    showToast("No data available to export.", "warning");
    return;
  }

  const headers = ["Invoice Number", "Vendor", "PO Number", "Amount (INR)", "Date", "Status", "Risk Level", "Risk Score", "Approval State", "AI Reason"];
  const rows = allHistory.map(item => {
    const inv = item.invoice || {};
    return [
      `"${inv.invoice_number || ''}"`,
      `"${inv.vendor_name || ''}"`,
      `"${inv.po_number || ''}"`,
      inv.total_amount || 0,
      `"${inv.invoice_date || ''}"`,
      `"${item.status || ''}"`,
      `"${item.risk_level || ''}"`,
      item.risk_score || 0,
      `"${item.human_action || ''}"`,
      `"${(item.ai_reason || '').replace(/"/g, '""')}"`
    ];
  });

  const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `recon_ai_audit_export_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  showToast("CSV export downloaded successfully!", "success");
}

function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}
