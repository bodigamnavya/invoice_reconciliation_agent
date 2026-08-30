/**
 * RECON AI - VENDOR RISK PROFILE CONTROLLER (vendor.js)
 * Implements Feature 2: Vendor Risk Profile, Analytics & Historical Tracking
 */

let vendorStatusChart = null;
let currentVendorId = null;

document.addEventListener("DOMContentLoaded", () => {
  Auth.requireAuth();

  const urlParams = new URLSearchParams(window.location.search);
  const paramId = urlParams.get("id");

  loadVendorList(paramId);

  const vendorSelect = document.getElementById("vendor-select");
  if (vendorSelect) {
    vendorSelect.addEventListener("change", (e) => {
      const selectedId = e.target.value;
      if (selectedId) {
        currentVendorId = selectedId;
        loadVendorProfile(selectedId);
      }
    });
  }
});

async function loadVendorList(preferredId) {
  try {
    const res = await fetch(`${CONFIG.API_BASE}/vendors`, {
      headers: {
        "Authorization": `Bearer ${Auth.getToken()}`
      }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || "Failed to load vendors.");

    const vendors = data.vendors || [];
    const select = document.getElementById("vendor-select");

    if (vendors.length === 0) {
      select.innerHTML = `<option value="">No vendors found</option>`;
      return;
    }

    select.innerHTML = vendors.map(v => `
      <option value="${v.id}" ${preferredId && String(preferredId) === String(v.id) ? 'selected' : ''}>
        ${v.name} (Risk: ${v.vendor_risk_score}/100)
      </option>
    `).join("");

    currentVendorId = preferredId || (vendors[0] ? vendors[0].id : null);
    if (currentVendorId) {
      select.value = currentVendorId;
      loadVendorProfile(currentVendorId);
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function loadVendorProfile(vendorId) {
  try {
    const [profileRes, historyRes] = await Promise.all([
      fetch(`${CONFIG.API_BASE}/vendors/${vendorId}/profile`, {
        headers: { "Authorization": `Bearer ${Auth.getToken()}` }
      }),
      fetch(`${CONFIG.API_BASE}/vendors/${vendorId}/history`, {
        headers: { "Authorization": `Bearer ${Auth.getToken()}` }
      })
    ]);

    const profileData = await profileRes.json();
    const historyData = await historyRes.json();

    if (!profileRes.ok) throw new Error(profileData.error || "Failed to load vendor profile.");
    if (!historyRes.ok) throw new Error(historyData.error || "Failed to load vendor history.");

    renderVendorProfile(profileData.vendor);
    renderVendorAnalytics(profileData.vendor);
    renderVendorHistory(historyData.invoices || []);
  } catch (err) {
    showToast(err.message, "error");
  }
}

function renderVendorProfile(v) {
  if (!v) return;

  document.getElementById("profile-vendor-name").textContent = v.name || "Vendor";
  document.getElementById("profile-vendor-address").textContent = v.address || "India";
  document.getElementById("profile-vendor-gstin").textContent = v.tax_id || "GSTIN29AAACA0001Z1";
  document.getElementById("profile-vendor-category").textContent = v.category || "Technology";

  document.getElementById("profile-risk-score-val").textContent = `${v.vendor_risk_score || 0}/100`;
  document.getElementById("profile-risk-level-badge").innerHTML = getRiskBadge(v.risk_level || "LOW");

  document.getElementById("profile-total-invoices").textContent = v.total_invoices || 0;
  document.getElementById("profile-total-value").textContent = formatCurrency(v.total_value || 0);
  document.getElementById("profile-avg-value").textContent = formatCurrency(v.average_value || 0);

  const cleanRate = v.total_invoices > 0 ? Math.round((v.matched_count / v.total_invoices) * 100) : 0;
  document.getElementById("profile-match-rate").textContent = `${cleanRate}%`;

  // Risk Vector Counters
  document.getElementById("stat-mismatches").textContent = v.mismatch_count || 0;
  document.getElementById("stat-duplicates").textContent = v.duplicate_count || 0;
  document.getElementById("stat-anomalies").textContent = v.anomaly_count || 0;
  document.getElementById("stat-baseline-avg").textContent = formatCurrency(v.average_invoice_amount || v.average_value || 0);
}

function renderVendorAnalytics(v) {
  const ctx = document.getElementById("vendorStatusChart");
  if (!ctx) return;

  const matched = v.matched_count || 0;
  const review = v.review_count || 0;
  const highRisk = v.high_risk_count || 0;
  const rejected = v.reject_count || 0;

  if (vendorStatusChart) {
    vendorStatusChart.destroy();
  }

  vendorStatusChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Matched", "Review Required", "High Risk", "Rejected"],
      datasets: [{
        data: [matched, review, highRisk, rejected],
        backgroundColor: [
          "#22c55e", // Green
          "#f59e0b", // Amber
          "#ef4444", // Red
          "#991b1b"  // Dark Red
        ],
        borderWidth: 0,
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#94a3b8",
            boxWidth: 12,
            padding: 14,
            font: { size: 11, family: "'Inter', sans-serif" }
          }
        }
      },
      cutout: "68%"
    }
  });
}

function renderVendorHistory(invoices) {
  const tbody = document.getElementById("vendor-history-tbody");
  if (!tbody) return;

  if (invoices.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No historical invoices on record for this vendor.</td></tr>`;
    return;
  }

  tbody.innerHTML = invoices.map(inv => {
    const recon = inv.reconciliation || {};
    const statusHtml = getStatusBadge(recon.status || "UNRECONCILED");
    const riskHtml = getRiskBadge(recon.risk_level || "LOW");
    const riskScore = recon.risk_score !== undefined ? `${recon.risk_score}/100` : "--";

    return `
      <tr>
        <td class="font-semibold mono" style="color: #38bdf8;">${inv.invoice_number}</td>
        <td>${formatDate(inv.invoice_date)}</td>
        <td class="mono">${inv.po_number || 'N/A'}</td>
        <td class="font-semibold">${formatCurrency(inv.total_amount)}</td>
        <td>${statusHtml}</td>
        <td>${riskHtml}</td>
        <td class="mono font-semibold">${riskScore}</td>
        <td>
          <a href="reconciliation.html?id=${inv.id}" class="btn-recon btn-recon-primary btn-sm">
            <i class="bi bi-eye"></i> Inspect
          </a>
        </td>
      </tr>
    `;
  }).join("");
}
