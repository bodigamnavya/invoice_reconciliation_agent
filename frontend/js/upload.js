/**
 * RECON AI - INVOICE UPLOAD & MULTI-AGENT WORKFLOW CONTROLLER (upload.js)
 */

document.addEventListener("DOMContentLoaded", () => {
  Auth.requireAuth();
  setupUploadEvents();
});

function setupUploadEvents() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });
}

const STAGES = [
  { id: "step-reading", label: "Reading Invoice Document (OCR/PyMuPDF)", desc: "Extracting raw characters and token streams" },
  { id: "step-extracting", label: "Extracting Structured Information", desc: "Normalizing amounts, dates, line items & vendor identity" },
  { id: "step-matching", label: "Finding & Validating Purchase Order", desc: "Executing 2-way comparison with database PO register" },
  { id: "step-payment", label: "Checking Payment Disbursements", desc: "Querying banking ledger transactions & calculating balance gaps" },
  { id: "step-anomalies", label: "Detecting Anomalies & Duplicates", desc: "Computing statistical Z-scores and 5-factor risk score" },
  { id: "step-decision", label: "Generating Recommendation & Reason", desc: "Synthesizing AI reasoning and action plan" }
];

async function handleFileUpload(file) {
  const allowed = ["pdf", "png", "jpg", "jpeg", "webp"];
  const ext = file.name.split(".").pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast(`Invalid file format .${ext}. Please upload a PDF or image.`, "error");
    return;
  }

  // Show Pipeline Progress UI
  const uploadFormArea = document.getElementById("upload-form-area");
  const progressArea = document.getElementById("progress-area");
  const uploadedFileName = document.getElementById("uploaded-filename");

  if (uploadFormArea) uploadFormArea.style.display = "none";
  if (progressArea) progressArea.style.display = "block";
  if (uploadedFileName) uploadedFileName.textContent = file.name;

  // Prepare FormData
  const formData = new FormData();
  formData.append("file", file);

  // Start animated step progression while backend processes
  let currentStep = 0;
  const stepInterval = setInterval(() => {
    if (currentStep < STAGES.length - 1) {
      updateStepUI(currentStep, "completed");
      currentStep++;
      updateStepUI(currentStep, "active");
    }
  }, 400);

  updateStepUI(0, "active");

  try {
    const res = await fetch(`${CONFIG.API_BASE}/invoices/upload`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    clearInterval(stepInterval);

    if (!res.ok) throw new Error(data.message || "Failed to process invoice.");

    // Complete all steps in UI
    for (let i = 0; i < STAGES.length; i++) {
      updateStepUI(i, "completed");
    }

    showToast("Invoice processed and reconciled successfully!", "success");

    setTimeout(() => {
      window.location.href = `reconciliation.html?id=${data.invoice.id}`;
    }, 1000);
  } catch (err) {
    clearInterval(stepInterval);
    showToast(err.message, "error");
    if (uploadFormArea) uploadFormArea.style.display = "block";
    if (progressArea) progressArea.style.display = "none";
  }
}

function updateStepUI(index, status) {
  const step = STAGES[index];
  if (!step) return;
  const el = document.getElementById(step.id);
  if (!el) return;

  el.className = `step-item ${status}`;
  const icon = el.querySelector(".step-icon");
  if (icon) {
    if (status === "completed") {
      icon.innerHTML = `<i class="bi bi-check-lg"></i>`;
    } else if (status === "active") {
      icon.innerHTML = `<i class="bi bi-arrow-repeat spin"></i>`;
    } else {
      icon.textContent = index + 1;
    }
  }
}
