-- database/init.sql - Traffic Light Service Audit Schema

-- Create audit log table (append-only for regulatory compliance)
CREATE TABLE IF NOT EXISTS signal_audit_log (
    log_id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    intersection_id VARCHAR(100) NOT NULL,
    bus_id VARCHAR(100),
    priority_level VARCHAR(50),
    status VARCHAR(20) NOT NULL,
    details TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_signal_audit_timestamp
    ON signal_audit_log (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_signal_audit_intersection
    ON signal_audit_log (intersection_id);

CREATE INDEX IF NOT EXISTS idx_signal_audit_event_type
    ON signal_audit_log (event_type);

-- Prevent updates/deletes for immutability (regulatory requirement)
ALTER TABLE signal_audit_log ENABLE ROW LEVEL SECURITY;
