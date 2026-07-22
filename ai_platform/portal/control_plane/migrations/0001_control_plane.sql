BEGIN;

CREATE TABLE portal_bots (
    tenant_id TEXT NOT NULL,
    bot_id TEXT NOT NULL,
    name TEXT NOT NULL,
    spec_json TEXT NOT NULL,
    desired_state TEXT NOT NULL,
    observed_state TEXT NOT NULL,
    current_revision INTEGER NOT NULL CHECK (current_revision > 0),
    PRIMARY KEY (tenant_id, bot_id)
);

CREATE INDEX ix_portal_bots_tenant
    ON portal_bots (tenant_id);

CREATE TABLE portal_bot_config_revisions (
    tenant_id TEXT NOT NULL,
    bot_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    revision_id TEXT NOT NULL,
    revision_json TEXT NOT NULL,
    created_by_actor_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (tenant_id, bot_id, revision),
    CONSTRAINT uq_portal_revision_identity UNIQUE (tenant_id, revision_id),
    CONSTRAINT fk_portal_revision_bot
        FOREIGN KEY (tenant_id, bot_id)
        REFERENCES portal_bots (tenant_id, bot_id)
        ON DELETE RESTRICT
);

CREATE INDEX ix_portal_revisions_tenant_bot
    ON portal_bot_config_revisions (tenant_id, bot_id);

CREATE TABLE portal_audit_events (
    audit_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    action TEXT NOT NULL,
    result TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    event_json TEXT NOT NULL
);

CREATE INDEX ix_portal_audit_tenant_resource
    ON portal_audit_events (tenant_id, resource_type, resource_id);

CREATE TABLE portal_outbox_events (
    event_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    event_json TEXT NOT NULL,
    published_at TIMESTAMPTZ NULL
);

CREATE INDEX ix_portal_outbox_tenant_aggregate
    ON portal_outbox_events (tenant_id, aggregate_type, aggregate_id);

CREATE INDEX ix_portal_outbox_unpublished
    ON portal_outbox_events (published_at);

COMMIT;
