-- AegisGov Database Schema
-- PostgreSQL 16
--
-- Tables: customers, orders, payments (business)
--         approval_requests, audit_events (governance)
--
-- Roles: order_reader, billing_reader, billing_writer, admin_writer
-- These roles are assigned by the Secure Tool Gateway (Phase 3).
-- The gateway selects the minimum required role per tool invocation.
-- Agents never receive direct database credentials.

-- ─── Least-Privilege Roles ─────────────────────────────────────────────────

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'order_reader') THEN
        CREATE ROLE order_reader;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'billing_reader') THEN
        CREATE ROLE billing_reader;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'billing_writer') THEN
        CREATE ROLE billing_writer;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin_writer') THEN
        CREATE ROLE admin_writer;
    END IF;
END
$$;

-- ─── Business Tables ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customers (
    id          SERIAL PRIMARY KEY,
    email       TEXT        NOT NULL UNIQUE,
    full_name   TEXT        NOT NULL,
    phone       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id              SERIAL      PRIMARY KEY,
    customer_id     INTEGER     NOT NULL REFERENCES customers(id),
    status          TEXT        NOT NULL DEFAULT 'ACTIVE',
    total_amount    NUMERIC(10,2) NOT NULL,
    currency        TEXT        NOT NULL DEFAULT 'USD',
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT orders_status_check CHECK (status IN ('ACTIVE', 'CANCELLED', 'REFUNDED'))
);

CREATE TABLE IF NOT EXISTS payments (
    id              SERIAL      PRIMARY KEY,
    order_id        INTEGER     NOT NULL REFERENCES orders(id),
    customer_id     INTEGER     NOT NULL REFERENCES customers(id),
    amount          NUMERIC(10,2) NOT NULL,
    currency        TEXT        NOT NULL DEFAULT 'USD',
    status          TEXT        NOT NULL DEFAULT 'COMPLETED',
    payment_method  TEXT        NOT NULL DEFAULT 'CARD',
    refund_amount   NUMERIC(10,2),
    refund_reason   TEXT,
    refunded_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT payments_status_check CHECK (status IN ('PENDING', 'COMPLETED', 'REFUNDED', 'FAILED'))
);

-- ─── Governance Tables ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS approval_requests (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id           TEXT        NOT NULL,
    agent_id            TEXT        NOT NULL,
    user_id             TEXT        NOT NULL,
    tool_name           TEXT        NOT NULL,
    arguments           JSONB       NOT NULL DEFAULT '{}',
    risk_level          TEXT        NOT NULL,
    status              TEXT        NOT NULL DEFAULT 'PENDING',
    approved_by         TEXT,
    resolution_reason   TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ,
    CONSTRAINT approval_requests_status_check CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    CONSTRAINT approval_requests_risk_check CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
);

CREATE TABLE IF NOT EXISTS audit_events (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id    TEXT        NOT NULL,
    user_id     TEXT        NOT NULL,
    agent_id    TEXT        NOT NULL,
    action_type TEXT        NOT NULL,
    decision    TEXT        NOT NULL,
    reason      TEXT,
    payload     JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT audit_events_decision_check CHECK (
        decision IN ('ALLOWED', 'DENIED', 'BLOCKED', 'PENDING', 'APPROVED', 'REJECTED')
    )
);

-- ─── Indexes ────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_orders_customer_id     ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_payments_order_id      ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_customer_id   ON payments(customer_id);

CREATE INDEX IF NOT EXISTS idx_approval_requests_status     ON approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_approval_requests_user_id    ON approval_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_thread_id  ON approval_requests(thread_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_created_at ON approval_requests(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_events_trace_id   ON audit_events(trace_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_user_id    ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_agent_id   ON audit_events(agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_decision   ON audit_events(decision);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at DESC);

-- ─── Least-Privilege Grants ─────────────────────────────────────────────────

-- order_reader: get_order, get_customer tools
GRANT SELECT ON customers, orders TO order_reader;

-- billing_reader: get_payment tool
GRANT SELECT ON orders, payments TO billing_reader;

-- billing_writer: issue_refund tool
GRANT SELECT ON orders, payments TO billing_writer;
GRANT UPDATE ON payments TO billing_writer;

-- admin_writer: delete_customer tool
GRANT SELECT ON customers, orders TO admin_writer;
GRANT DELETE ON customers TO admin_writer;

-- Governance tables: application user only
GRANT ALL ON approval_requests, audit_events TO aegisgov;

-- Sequence grants for INSERT operations
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public
    TO billing_writer, admin_writer;

-- ─── Demo Seed Data ─────────────────────────────────────────────────────────
-- Deterministic data supporting the four mandatory test scenarios:
--   Test 1:  get_order(421)
--   Test 2:  analyst attempts delete_customer (blocked by OPA)
--   Test 3:  prompt injection (blocked before DB)
--   Test 4:  admin delete_customer(42) → HITL → execute
--
-- Additional:
--   issue_refund(order=8829, amount=120)  → AUTO (≤ $500)
--   issue_refund(order=8829, amount=700)  → HITL (> $500)

INSERT INTO customers (id, email, full_name, phone)
VALUES
    (1,  'alice.johnson@example.com',  'Alice Johnson',  '+1-555-0101'),
    (42, 'bob.martinez@example.com',   'Bob Martinez',   '+1-555-0142'),
    (99, 'carol.smith@example.com',    'Carol Smith',    '+1-555-0199')
ON CONFLICT (id) DO NOTHING;

INSERT INTO orders (id, customer_id, status, total_amount, description)
VALUES
    (421,  1,  'ACTIVE', 299.99, 'Premium widget bundle'),
    (8829, 42, 'ACTIVE', 850.00, 'Enterprise software license'),
    (9001, 42, 'ACTIVE', 150.00, 'Standard support package'),
    (9002, 99, 'ACTIVE', 75.00,  'Monthly subscription')
ON CONFLICT (id) DO NOTHING;

INSERT INTO payments (id, order_id, customer_id, amount, status, payment_method)
VALUES
    (1, 421,  1,  299.99, 'COMPLETED', 'CARD'),
    (2, 8829, 42, 850.00, 'COMPLETED', 'CARD'),
    (3, 9001, 42, 150.00, 'COMPLETED', 'BANK_TRANSFER'),
    (4, 9002, 99,  75.00, 'COMPLETED', 'CARD')
ON CONFLICT (id) DO NOTHING;

-- Advance sequences past the seeded IDs so future inserts don't conflict
SELECT setval('customers_id_seq', GREATEST((SELECT MAX(id) FROM customers), 1000));
SELECT setval('orders_id_seq',    GREATEST((SELECT MAX(id) FROM orders),    10000));
SELECT setval('payments_id_seq',  GREATEST((SELECT MAX(id) FROM payments),  10000));
