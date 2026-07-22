BEGIN;

CREATE TABLE portal_event_inbox (
    consumer_name TEXT NOT NULL,
    event_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (consumer_name, event_id)
);

CREATE INDEX ix_portal_event_inbox_tenant
    ON portal_event_inbox (tenant_id);

CREATE INDEX ix_portal_event_inbox_correlation
    ON portal_event_inbox (correlation_id);

COMMIT;
