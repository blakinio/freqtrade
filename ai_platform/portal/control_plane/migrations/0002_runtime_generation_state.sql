BEGIN;

ALTER TABLE portal_bots
    ADD COLUMN latest_authored_revision_id TEXT NULL,
    ADD COLUMN desired_revision_id TEXT NULL,
    ADD COLUMN desired_runtime_generation_id TEXT NULL,
    ADD COLUMN observed_runtime_generation_id TEXT NULL,
    ADD COLUMN state_version INTEGER NULL;

CREATE TABLE portal_runtime_generations (
    generation_id TEXT PRIMARY KEY,
    generation_ordinal INTEGER NOT NULL,
    tenant_id TEXT NOT NULL,
    bot_id TEXT NOT NULL,
    config_revision_id TEXT NOT NULL,
    config_revision_number INTEGER NOT NULL,
    config_revision_digest TEXT NOT NULL,
    normalized_runtime_config_digest TEXT NOT NULL,
    runtime_image_digest TEXT NOT NULL,
    strategy_version TEXT NOT NULL,
    strategy_artifact_digest TEXT NOT NULL,
    model_version TEXT NULL,
    model_artifact_digest TEXT NULL,
    feature_schema_version TEXT NULL,
    risk_policy_version TEXT NOT NULL,
    risk_policy_digest TEXT NOT NULL,
    execution_mode TEXT NOT NULL,
    exchange_mode TEXT NOT NULL,
    exchange_connection_revision TEXT NULL,
    isolation_profile_version TEXT NOT NULL,
    isolation_profile_digest TEXT NOT NULL,
    gateway_contract_version TEXT NOT NULL,
    generation_spec_version TEXT NOT NULL,
    generation_spec_digest TEXT NOT NULL,
    created_by_actor_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    request_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    causation_id TEXT NULL,
    CONSTRAINT fk_portal_runtime_generation_bot
        FOREIGN KEY (tenant_id, bot_id)
        REFERENCES portal_bots (tenant_id, bot_id)
        ON DELETE RESTRICT,
    CONSTRAINT uq_portal_runtime_generation_ordinal
        UNIQUE (tenant_id, bot_id, generation_ordinal)
);

CREATE INDEX ix_portal_runtime_generation_bot
    ON portal_runtime_generations (tenant_id, bot_id);

CREATE TABLE portal_bot_rollouts (
    rollout_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    bot_id TEXT NOT NULL,
    from_generation_id TEXT NULL,
    to_generation_id TEXT NOT NULL,
    status TEXT NOT NULL,
    reason_code TEXT NULL,
    requested_by_actor_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NULL,
    CONSTRAINT fk_portal_rollout_bot
        FOREIGN KEY (tenant_id, bot_id)
        REFERENCES portal_bots (tenant_id, bot_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_portal_rollout_to_generation
        FOREIGN KEY (to_generation_id)
        REFERENCES portal_runtime_generations (generation_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_portal_rollout_from_generation
        FOREIGN KEY (from_generation_id)
        REFERENCES portal_runtime_generations (generation_id)
        ON DELETE RESTRICT,
    CONSTRAINT uq_portal_rollout_idempotency
        UNIQUE (tenant_id, bot_id, idempotency_key)
);

CREATE INDEX ix_portal_rollout_bot
    ON portal_bot_rollouts (tenant_id, bot_id);

CREATE TABLE portal_runtime_generation_observations (
    observation_id TEXT PRIMARY KEY,
    generation_id TEXT NOT NULL,
    runtime_instance_id TEXT NOT NULL,
    reconciliation_epoch INTEGER NOT NULL,
    reconciliation_attempt INTEGER NOT NULL,
    observed_state TEXT NOT NULL,
    observed_generation_spec_digest TEXT NOT NULL,
    observed_image_digest TEXT NOT NULL,
    observed_config_digest TEXT NOT NULL,
    source_sequence INTEGER NULL,
    source_version TEXT NULL,
    source_observed_at TIMESTAMPTZ NULL,
    reconciled_at TIMESTAMPTZ NOT NULL,
    identity_status TEXT NOT NULL,
    freshness_status TEXT NOT NULL,
    completeness_status TEXT NOT NULL,
    evidence_hash TEXT NOT NULL,
    reason_code TEXT NULL,
    CONSTRAINT fk_portal_runtime_observation_generation
        FOREIGN KEY (generation_id)
        REFERENCES portal_runtime_generations (generation_id)
        ON DELETE RESTRICT
);

CREATE INDEX ix_portal_runtime_observation_generation
    ON portal_runtime_generation_observations (generation_id, reconciled_at);

CREATE TABLE portal_command_idempotency (
    tenant_id TEXT NOT NULL,
    bot_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    operation TEXT NOT NULL,
    semantic_request_digest TEXT NOT NULL,
    generation_id TEXT NOT NULL,
    rollout_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (tenant_id, bot_id, idempotency_key),
    CONSTRAINT fk_portal_command_idempotency_bot
        FOREIGN KEY (tenant_id, bot_id)
        REFERENCES portal_bots (tenant_id, bot_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_portal_command_idempotency_generation
        FOREIGN KEY (generation_id)
        REFERENCES portal_runtime_generations (generation_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_portal_command_idempotency_rollout
        FOREIGN KEY (rollout_id)
        REFERENCES portal_bot_rollouts (rollout_id)
        ON DELETE RESTRICT
);

COMMIT;
