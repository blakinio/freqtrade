CREATE TABLE portal_execution_submissions (
    tenant_id VARCHAR(255) NOT NULL,
    attempt_id VARCHAR(255) NOT NULL,
    idempotency_key VARCHAR(255) NOT NULL,
    command_id VARCHAR(255) NOT NULL,
    execution_intent_id VARCHAR(36) NOT NULL,
    submission_digest VARCHAR(64) NOT NULL,
    submission_json TEXT NOT NULL,
    receipt_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (tenant_id, attempt_id),
    CONSTRAINT uq_portal_execution_submission_idempotency
        UNIQUE (tenant_id, idempotency_key),
    CONSTRAINT uq_portal_execution_submission_command
        UNIQUE (tenant_id, command_id),
    CONSTRAINT uq_portal_execution_submission_intent
        UNIQUE (tenant_id, execution_intent_id)
);

CREATE INDEX ix_portal_execution_submissions_tenant_updated
    ON portal_execution_submissions (tenant_id, updated_at);
