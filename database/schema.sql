-- =========================================================
-- Invoice-to-Payment Reconciliation Agent Database Schema
-- Database: PostgreSQL (with ANSI SQL compatibility)
-- =========================================================

-- Enable UUID extension if supported
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Clean up existing tables (reverse order of dependencies)
DROP TABLE IF EXISTS reconciliation_results CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS purchase_orders CASCADE;
DROP TABLE IF EXISTS vendors CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. USERS TABLE
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'Finance Analyst',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. VENDORS TABLE
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    tax_id VARCHAR(50),
    email VARCHAR(150),
    phone VARCHAR(50),
    address TEXT,
    average_invoice_amount NUMERIC(15, 2) DEFAULT 0.00,
    historical_invoice_count INT DEFAULT 0,
    risk_rating VARCHAR(30) DEFAULT 'LOW', -- LOW, MEDIUM, HIGH
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. PURCHASE ORDERS TABLE
CREATE TABLE purchase_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(100) UNIQUE NOT NULL,
    vendor_id INT REFERENCES vendors(id) ON DELETE SET NULL,
    vendor_name VARCHAR(200) NOT NULL,
    po_date DATE NOT NULL,
    subtotal NUMERIC(15, 2) DEFAULT 0.00,
    tax_amount NUMERIC(15, 2) DEFAULT 0.00,
    total_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    status VARCHAR(50) DEFAULT 'APPROVED', -- APPROVED, CLOSED, PENDING, REJECTED
    line_items TEXT, -- JSON formatted array of itemized goods/services
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. INVOICES TABLE
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(100) NOT NULL,
    vendor_id INT REFERENCES vendors(id) ON DELETE SET NULL,
    vendor_name VARCHAR(200) NOT NULL,
    po_id INT REFERENCES purchase_orders(id) ON DELETE SET NULL,
    po_number VARCHAR(100),
    invoice_date DATE NOT NULL,
    due_date DATE,
    subtotal NUMERIC(15, 2) DEFAULT 0.00,
    tax_amount NUMERIC(15, 2) DEFAULT 0.00,
    total_amount NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    line_items TEXT, -- JSON formatted array of line items
    raw_extracted_text TEXT,
    file_path VARCHAR(255),
    file_name VARCHAR(255),
    file_type VARCHAR(50),
    upload_status VARCHAR(50) DEFAULT 'PROCESSED', -- PENDING, PROCESSED, FAILED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. PAYMENTS TABLE
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    payment_reference VARCHAR(100) UNIQUE NOT NULL,
    invoice_id INT REFERENCES invoices(id) ON DELETE SET NULL,
    invoice_number VARCHAR(100),
    po_id INT REFERENCES purchase_orders(id) ON DELETE SET NULL,
    po_number VARCHAR(100),
    vendor_id INT REFERENCES vendors(id) ON DELETE SET NULL,
    vendor_name VARCHAR(200) NOT NULL,
    payment_date DATE NOT NULL,
    amount_paid NUMERIC(15, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    payment_method VARCHAR(50) DEFAULT 'BANK_TRANSFER', -- BANK_TRANSFER, UPI, NEFT, RTGS, CHEQUE, CARD
    status VARCHAR(50) DEFAULT 'COMPLETED', -- COMPLETED, PENDING, FAILED
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. RECONCILIATION RESULTS TABLE
CREATE TABLE reconciliation_results (
    id SERIAL PRIMARY KEY,
    invoice_id INT NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    po_id INT REFERENCES purchase_orders(id) ON DELETE SET NULL,
    payment_id INT REFERENCES payments(id) ON DELETE SET NULL,
    
    -- Status and classifications
    status VARCHAR(50) NOT NULL, -- MATCHED, REVIEW_REQUIRED, HIGH_RISK, REJECT
    po_match_status VARCHAR(50) NOT NULL, -- MATCHED, MISMATCH, NOT_FOUND
    payment_match_status VARCHAR(50) NOT NULL, -- FULL_PAYMENT, PARTIAL_PAYMENT, OVERPAYMENT, UNPAID
    duplicate_status VARCHAR(50) DEFAULT 'UNIQUE', -- UNIQUE, DUPLICATE_FOUND
    anomaly_status VARCHAR(50) DEFAULT 'NORMAL', -- NORMAL, ANOMALY_DETECTED
    
    -- Numerical evaluations
    risk_score INT NOT NULL, -- 0 to 100
    risk_level VARCHAR(30) NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
    confidence_score NUMERIC(5, 2) DEFAULT 95.00,
    
    -- Discrepancy analysis
    amount_difference_po NUMERIC(15, 2) DEFAULT 0.00,
    amount_difference_payment NUMERIC(15, 2) DEFAULT 0.00,
    risk_breakdown TEXT, -- JSON structured reasons and factor weights
    
    -- AI Generated Insights
    ai_reason TEXT,
    ai_explanation TEXT NOT NULL,
    ai_recommendation TEXT NOT NULL,
    
    -- Human Approval Loop
    human_action VARCHAR(50) DEFAULT 'PENDING', -- PENDING, APPROVED, REVIEWED, REJECTED
    reviewed_by INT REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP,
    reviewer_notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES for fast reporting and queries
CREATE INDEX idx_invoices_vendor_id ON invoices(vendor_id);
CREATE INDEX idx_invoices_po_number ON invoices(po_number);
CREATE INDEX idx_invoices_invoice_number ON invoices(invoice_number);
CREATE INDEX idx_reconciliation_invoice_id ON reconciliation_results(invoice_id);
CREATE INDEX idx_reconciliation_status ON reconciliation_results(status);
CREATE INDEX idx_reconciliation_risk_level ON reconciliation_results(risk_level);
CREATE INDEX idx_payments_invoice_number ON payments(invoice_number);
CREATE INDEX idx_purchase_orders_po_number ON purchase_orders(po_number);
