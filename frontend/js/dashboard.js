/**
 * RECON AI - DASHBOARD CONTROLLER (dashboard.js)
 */

let monthlyChart = null;
let riskChart = null;

document.addEventListener("DOMContentLoaded", () => {
  Auth.requireAuth();
  loadDashboardData();
});

async function loadDashboardData() {
  try {
    const res = await fetch(`${CONFIG.API_BASE}/dashboard`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || "Failed to load dashboard.");

    renderKPIs(data.metrics);
    renderCharts(data.risk_distribution, data.monthly_trends);
    renderRecentTable(data.recent_reconciliations);
  } catch (err) {
    showToast(err.message, "error");
  }
}

function renderKPIs(metrics) {
  if (!metrics) return;
  document.getElementById("kpi-total-invoices").textContent = metrics.total_invoices || 0;
  document.getElementById("kpi-matched").textContent = metrics.matched_invoices || 0;
  document.getElementById("kpi-mismatches").textContent = metrics.mismatches || 0;
  document.getElementById("kpi-high-risk").textContent = metrics.high_risk_invoices || 0;
  document.getElementById("kpi-pending-approvals").textContent = metrics.pending_approvals || 0;
  if (document.getElementById("kpi-total-value")) {
    document.getElementById("kpi-total-value").textContent = formatCurrency(metrics.total_invoice_amount);
  }
}

function renderCharts(riskDist, monthlyTrends) {
  // 1. Monthly Trends Bar Chart
  const ctxTrends = document.getElementById("monthlyTrendsChart");
  if (ctxTrends) {
    const labels = (monthlyTrends || []).map(t => t.month);
    const matchedData = (monthlyTrends || []).map(t => t.matched);
    const mismatchData = (monthlyTrends || []).map(t => t.mismatches);

    if (monthlyChart) monthlyChart.destroy();
    monthlyChart = new Chart(ctxTrends, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Matched",
            data: matchedData,
            backgroundColor: "#10b981",
            borderRadius: 6,
          },
          {
            label: "Mismatches / High-Risk",
            data: mismatchData,
            backgroundColor: "#f59e0b",
            borderRadius: 6,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "top", labels: { boxWidth: 12, font: { family: "Plus Jakarta Sans", size: 12 } } }
        },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, grid: { color: "#f1f5f9" } }
        }
      }
    });
  }

  // 2. Risk Distribution Doughnut Chart
  const ctxRisk = document.getElementById("riskDistributionChart");
  if (ctxRisk) {
    const low = (riskDist && riskDist.LOW) || 0;
    const med = (riskDist && riskDist.MEDIUM) || 0;
    const high = (riskDist && riskDist.HIGH) || 0;
    const crit = (riskDist && riskDist.CRITICAL) || 0;

    if (riskChart) riskChart.destroy();
    riskChart = new Chart(ctxRisk, {
      type: "doughnut",
      data: {
        labels: ["Low Risk", "Medium Risk", "High Risk", "Critical Risk"],
        datasets: [{
          data: [low, med, high, crit],
          backgroundColor: ["#10b981", "#f59e0b", "#f97316", "#ef4444"],
          borderWidth: 2,
          borderColor: "#ffffff"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { boxWidth: 10, font: { family: "Plus Jakarta Sans", size: 11 } } }
        },
        cutout: "68%"
      }
    });
  }
}

function renderRecentTable(reconciliations) {
  const tbody = document.getElementById("recent-reconciliations-body");
  if (!tbody) return;

  if (!reconciliations || reconciliations.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No reconciliations found.</td></tr>`;
    return;
  }

  tbody.innerHTML = reconciliations.map(item => {
    const inv = item.invoice || {};
    const amount = formatCurrency(inv.total_amount || 0);
    const invoiceNum = inv.invoice_number || `INV-${item.invoice_id}`;
    const vendor = inv.vendor_name || "Unknown Vendor";
    const statusBadge = getStatusBadge(item.status);
    const riskBadge = getRiskBadge(item.risk_level);
    const dateStr = formatDate(item.created_at);

    return `
      <tr>
        <td class="mono font-semibold">${invoiceNum}</td>
        <td>${vendor}</td>
        <td class="font-semibold">${amount}</td>
        <td>${statusBadge}</td>
        <td>${riskBadge}</td>
        <td>
          <span class="badge ${item.human_action === 'APPROVED' ? 'bg-success' : item.human_action === 'REJECTED' ? 'bg-danger' : item.human_action === 'REVIEWED' ? 'bg-warning text-dark' : 'bg-light text-dark border'}">
            ${item.human_action || 'PENDING'}
          </span>
        </td>
        <td class="text-end">
          <a href="reconciliation.html?id=${item.invoice_id}" class="btn-recon btn-recon-outline btn-sm">
            <i class="bi bi-search"></i> Inspect
          </a>
        </td>
      </tr>
    `;
  }).join("");
}
