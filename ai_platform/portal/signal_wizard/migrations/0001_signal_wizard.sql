CREATE TABLE IF NOT EXISTS portal_signal_wizard_previews (
    tenant_id VARCHAR(255) NOT NULL,
    preview_hash VARCHAR(64) NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    request_digest VARCHAR(64) NOT NULL,
    strategy_version VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    preview_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, preview_hash),
    CONSTRAINT uq_portal_signal_wizard_preview_tenant_idempotency
        UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS ix_portal_signal_wizard_preview_created_at
    ON portal_signal_wizard_previews (created_at);

CREATE TABLE IF NOT EXISTS portal_signal_wizard_submissions (
    tenant_id VARCHAR(255) NOT NULL,
    experiment_id VARCHAR(36) NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    request_digest VARCHAR(64) NOT NULL,
    preview_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    submission_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, experiment_id),
    CONSTRAINT uq_portal_signal_wizard_submit_tenant_idempotency
        UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS ix_portal_signal_wizard_submit_preview_hash
    ON portal_signal_wizard_submissions (preview_hash);
CREATE INDEX IF NOT EXISTS ix_portal_signal_wizard_submit_created_at
    ON portal_signal_wizard_submissions (created_at);
