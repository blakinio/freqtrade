BEGIN;

CREATE TABLE portal_bot_commands (
    scope_tenant_id VARCHAR(255) NOT NULL,
    command_id VARCHAR(255) NOT NULL,
    idempotency_key VARCHAR(255) NOT NULL,
    command_kind VARCHAR(32) NOT NULL,
    command_digest VARCHAR(64) NOT NULL,
    command_json TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (scope_tenant_id, command_id),
    CONSTRAINT uq_portal_bot_command_idempotency
        UNIQUE (scope_tenant_id, idempotency_key)
);

CREATE INDEX ix_portal_bot_commands_tenant_created
    ON portal_bot_commands (scope_tenant_id, created_at);

CREATE TABLE portal_bot_command_history (
    history_id VARCHAR(36) PRIMARY KEY,
    scope_tenant_id VARCHAR(255) NOT NULL,
    command_id VARCHAR(255) NOT NULL,
    sequence INTEGER NOT NULL,
    entry_json TEXT NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT uq_portal_bot_command_history_sequence
        UNIQUE (scope_tenant_id, command_id, sequence),
    CONSTRAINT fk_portal_bot_command_history_command
        FOREIGN KEY (scope_tenant_id, command_id)
        REFERENCES portal_bot_commands (scope_tenant_id, command_id)
        ON DELETE RESTRICT
);

CREATE INDEX ix_portal_bot_command_history_tenant_command
    ON portal_bot_command_history (scope_tenant_id, command_id, sequence);

CREATE TABLE portal_bot_command_idempotency_conflicts (
    conflict_id VARCHAR(36) PRIMARY KEY,
    scope_tenant_id VARCHAR(255) NOT NULL,
    idempotency_key VARCHAR(255) NOT NULL,
    existing_command_id VARCHAR(255) NOT NULL,
    attempted_command_id VARCHAR(255) NOT NULL,
    conflict_json TEXT NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT fk_portal_bot_command_conflict_existing
        FOREIGN KEY (scope_tenant_id, existing_command_id)
        REFERENCES portal_bot_commands (scope_tenant_id, command_id)
        ON DELETE RESTRICT
);

CREATE INDEX ix_portal_bot_command_conflicts_tenant_key
    ON portal_bot_command_idempotency_conflicts (
        scope_tenant_id,
        idempotency_key,
        recorded_at
    );

COMMIT;
