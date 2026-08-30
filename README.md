# 🚀 Invoice-to-Payment Reconciliation Agent (ReconAI)

An autonomous, enterprise-grade AI financial reconciliation platform that automatically ingests multi-format invoices, extracts structured line items, matches invoices against Purchase Orders and Payment records, detects anomalies, duplicate invoices, and calculates a 0–100 risk score with natural language explanations and human-in-the-loop sign-off governance.

---

## 🌟 Architecture Overview

```
Invoice Upload (PDF/Image)
       │
       ▼
[ Invoice Agent & OCR Service ] ──▶ Structured Invoice Data (JSON)
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
[ Matching Agent (PO 2-Way) ]   [ Payment Agent (Banking Ledger) ]
       │                                 │
       └────────────────┬────────────────┘
                        ▼
            [ Risk Agent (5 Vectors) ]
       (Duplicates, Z-Score Anomaly, PO Gap, Payment Gap, Vendor Rating)
                        │
                        ▼
           [ Decision Agent & LLM Engine ]
     (MATCHED | REVIEW_REQUIRED | HIGH_RISK | REJECT)
     (Natural Language Reasoning & Action Recommendation)
                        │
                        ▼
       [ PostgreSQL Persistence & REST APIs ]
                        │
                        ▼
 [ Enterprise Frontend Command Center & Inspector ]
```

---

## 🤖 The 5 Multi-Agent Modules

| Agent | File | Responsibilities |
|---|---|---|
| **Invoice Agent** | `backend/agents/invoice_agent.py` | PyMuPDF & OCR text parsing, entity extraction (Vendor, Inv#, Dates, Subtotal, Tax, Total, Line Items, PO#). |
| **Matching Agent** | `backend/agents/matching_agent.py` | 2-way / 3-way matching against database Purchase Orders with percentage & absolute tolerance limits. |
| **Payment Agent** | `backend/agents/payment_agent.py` | Scans banking ledger disbursements; detects `FULL_PAYMENT`, `PARTIAL_PAYMENT`, `OVERPAYMENT`, or `UNPAID`. |
| **Risk Agent** | `backend/agents/risk_agent.py` | 5-vector fraud/risk scoring (Duplicates, Statistical Anomaly Z-Score > 2.0, PO Gap, Payment Shortfall, Vendor profile). |
| **Decision Agent** | `backend/agents/decision_agent.py` | Deterministic decision matrix + LLM/Rule generation of reason, explanation, and next action recommendation. |

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3 (Enterprise Dark Navy & Slate Design System), JavaScript ES6+, Bootstrap Icons, Chart.js.
- **Backend**: Python 3.12+, Flask, Flask-CORS, SQLAlchemy, PyJWT, Bcrypt.
- **Document AI**: PyMuPDF (`fitz`), ReportLab, Pandas, Scikit-learn.
- **LLM Intelligence**: Configurable Google Gemini / OpenAI with built-in high-precision deterministic Rule-Based reasoning engine.
- **Database**: PostgreSQL (with automatic zero-friction SQLite fallback for local developer machines).

---

## ⚡ Quick Start (Local Setup)

### 1. Clone & Install Dependencies

```bash
# Clone the repository
cd invoice-payment-reconciliation-agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment configuration:
```bash
cp .env.example .env
```

Configure your PostgreSQL database connection string in `.env`:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/invoice_reconciliation
SECRET_KEY=enterprise_finance_reconciliation_2026
LLM_PROVIDER=rule-based
# Optional: Set Gemini / OpenAI API key
LLM_API_KEY=
```
*(Note: If PostgreSQL is not active locally, the platform will automatically connect to a local SQLite database at `database/reconciliation.db` without crashing).*

### 3. Seed Database & Generate Sample Invoices

```bash
# Populate initial demo records (Vendors, POs, Payments, Invoices)
python -m database.seed_data

# Generate realistic sample PDF invoices in sample_data/invoices/
python -m sample_data.generate_samples
```

### 4. Launch Application

```bash
# Start the Flask backend server
python backend/app.py
```

Open your browser and navigate to:
👉 **`http://localhost:5000`**

---

## 🔑 Default Demo Credentials

| Role | Email | Password |
|---|---|---|
| **Senior Controller** | `admin@finance.ai` | `password123` |
| **Reconciliation Specialist** | `analyst@finance.ai` | `password123` |

*(A 1-click **Auto-fill Demo Credentials** button is also available on the Login screen).*

---

## 🎯 5 Core Demo Scenarios Walkthrough

The project comes pre-loaded with the 5 required reconciliation scenarios (also generated as sample PDFs in `sample_data/invoices/`):

1. **Scenario 1: Perfect Match**
   - **Vendor**: Apex Global Technologies
   - **Invoice**: `INV-2026-001` (₹1,50,000.00)
   - **PO**: `PO-2026-101` (₹1,50,000.00) | **Payment**: `PAY-TXN-984210` (₹1,50,000.00)
   - **Outcome**: `MATCHED` | **Risk Score**: 0/100 (LOW)

2. **Scenario 2: Payment Mismatch (Partial Payment)**
   - **Vendor**: Nova Solutions Pvt Ltd
   - **Invoice**: `INV-2026-002` (₹85,000.00)
   - **Payment**: `PAY-TXN-984211` (₹80,000.00 disbursed)
   - **Outcome**: `REVIEW_REQUIRED` | **Reason**: Shortfall balance of ₹5,000.00.

3. **Scenario 3: PO Mismatch (Price Variance)**
   - **Vendor**: Quantum Logistics Corp
   - **Invoice**: `INV-2026-003` (₹90,000.00)
   - **PO**: `PO-2026-103` (Authorized ₹85,000.00)
   - **Outcome**: `HIGH_RISK` | **Reason**: Unapproved surcharge exceeding PO limit.

4. **Scenario 4: Duplicate Invoice**
   - **Vendor**: Starlight Media Services
   - **Invoice**: `INV-2026-004` (Submitted second time)
   - **Outcome**: `REJECT` / `REVIEW_REQUIRED` | **Reason**: Duplicate invoice number already processed.

5. **Scenario 5: Statistical Amount Anomaly**
   - **Vendor**: Vertex Cloud Infra (Historical average: ₹45,000.00)
   - **Invoice**: `INV-2026-005` (Billed: ₹3,20,000.00)
   - **Outcome**: `ANOMALY / HIGH_RISK` | **Reason**: Z-score spike exceeding vendor baseline.

---

## 📡 REST API Reference

### Authentication
- `POST /api/auth/register` - Create user account
- `POST /api/auth/login` - Authenticate & obtain JWT
- `GET /api/auth/me` - Get current session profile

### Invoices & Reconciliation
- `POST /api/invoices/upload` - Upload PDF/Image, extract data, run agents, persist in DB
- `GET /api/invoices` - List all invoices
- `GET /api/reconciliation/<invoice_id>` - Fetch 3-way match, risk scores & AI explanation
- `POST /api/reconciliation/<invoice_id>/run` - Re-execute agentic pipeline
- `POST /api/reconciliation/<invoice_id>/approve` - Human sign-off & approval
- `POST /api/reconciliation/<invoice_id>/review` - Flag for controller audit
- `POST /api/reconciliation/<invoice_id>/reject` - Reject invoice

### Analytics & Diagnostics
- `GET /api/dashboard` - Real-time KPI counts, risk doughnut chart & monthly trends
- `GET /api/history` - Searchable audit history with status & risk filtering
- `GET /health` - Service health status
- `GET /db-health` - Persistent database connection health

---

## ☁️ Deployment Guide

### Deploying Backend (Render)
1. Create a **Web Service** on Render connected to this repository.
2. Set Environment: **Python 3**.
3. Build Command: `pip install -r backend/requirements.txt`.
4. Start Command: `gunicorn backend.app:app`.
5. Add Environment Variables:
   - `DATABASE_URL`: `postgresql://...` (from Render PostgreSQL or Supabase)
   - `SECRET_KEY`: `<your_production_secret>`
   - `LLM_PROVIDER`: `gemini` or `openai` or `rule-based`
   - `LLM_API_KEY`: `<your_api_key>`

### Deploying Frontend (Vercel)
1. Deploy the `frontend/` directory to Vercel.
2. In `frontend/js/config.js`, point `CONFIG.API_BASE` to your Render backend URL (e.g. `https://your-backend.onrender.com/api`).

---

## 🧪 Running Automated Unit Tests

```bash
python -m unittest discover tests
```

---

## 📄 License
MIT License. Built for enterprise autonomous financial reconciliation.
