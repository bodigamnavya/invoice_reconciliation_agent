/**
 * RECON AI - GLOBAL CONFIGURATION & HELPER UTILITIES (config.js)
 */

const CONFIG = {
  // Use relative /api if hosted from Flask, or fallback to localhost:5000 if opened on other port/static server
  API_BASE: window.location.origin.includes(":5000") || window.location.protocol.startsWith("http") 
    ? "/api" 
    : "http://127.0.0.1:5000/api",
  CURRENCY_SYMBOL: "₹",
};

/**
 * Toast Notification Utility
 */
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `recon-toast ${type}`;
  
  let icon = "info-circle";
  if (type === "success") icon = "check-circle";
  if (type === "error") icon = "exclamation-triangle";
  if (type === "warning") icon = "exclamation-circle";

  toast.innerHTML = `
    <i class="bi bi-${icon}" style="font-size: 1.25rem;"></i>
    <div style="flex: 1; font-size: 0.9rem;">${message}</div>
    <button type="button" style="background:none; border:none; color:#94a3b8; cursor:pointer;" onclick="this.parentElement.remove()">
      <i class="bi bi-x-lg"></i>
    </button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/**
 * Currency Formatter
 */
function formatCurrency(amount) {
  if (amount === null || amount === undefined || isNaN(amount)) return "₹0.00";
  const num = parseFloat(amount);
  return `${CONFIG.CURRENCY_SYMBOL}${num.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * Date Formatter
 */
function formatDate(dateStr) {
  if (!dateStr) return "N/A";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-IN", { year: "numeric", month: "short", day: "numeric" });
  } catch (e) {
    return dateStr;
  }
}

/**
 * Status and Risk Badge Formatters
 */
function getStatusBadge(status) {
  const s = (status || "").toUpperCase();
  if (s === "MATCHED") {
    return `<span class="badge-status badge-matched"><i class="bi bi-check-circle-fill"></i> Matched</span>`;
  } else if (s === "HIGH_RISK") {
    return `<span class="badge-status badge-high-risk"><i class="bi bi-shield-slash-fill"></i> High Risk</span>`;
  } else if (s === "REJECT") {
    return `<span class="badge-status badge-reject"><i class="bi bi-x-circle-fill"></i> Reject</span>`;
  } else {
    return `<span class="badge-status badge-review"><i class="bi bi-exclamation-circle-fill"></i> Review Required</span>`;
  }
}

function getRiskBadge(riskLevel) {
  const r = (riskLevel || "LOW").toUpperCase();
  if (r === "CRITICAL") return `<span class="badge-risk badge-risk-critical">Critical</span>`;
  if (r === "HIGH") return `<span class="badge-risk badge-risk-high">High</span>`;
  if (r === "MEDIUM") return `<span class="badge-risk badge-risk-medium">Medium</span>`;
  return `<span class="badge-risk badge-risk-low">Low</span>`;
}
