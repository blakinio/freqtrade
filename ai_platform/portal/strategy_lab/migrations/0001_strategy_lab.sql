CREATE TABLE IF NOT EXISTS portal_strategy_lab_experiments (
    tenant_id VARCHAR(255) NOT NULL,
    experiment_id VARCHAR(36) NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    request_digest VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    experiment_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, experiment_id),
    CONSTRAINT uq_portal_strategy_lab_tenant_idempotency
        UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS ix_portal_strategy_lab_status
    ON portal_strategy_lab_experiments (status);
CREATE INDEX IF NOT EXISTS ix_portal_strategy_lab_created_at
    ON portal_strategy_lab_experiments (created_at);
