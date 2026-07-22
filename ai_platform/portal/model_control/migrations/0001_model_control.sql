BEGIN;

CREATE TABLE portal_model_versions (
    tenant_id TEXT NOT NULL,
    model_version_id TEXT NOT NULL,
    model_family_id TEXT NOT NULL,
    model_json TEXT NOT NULL,
    registered_by_actor_id TEXT NOT NULL,
    registered_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (tenant_id, model_version_id)
);

CREATE INDEX ix_portal_model_versions_tenant_family
    ON portal_model_versions (tenant_id, model_family_id);

CREATE TABLE portal_model_promotion_slots (
    tenant_id TEXT NOT NULL,
    model_family_id TEXT NOT NULL,
    environment TEXT NOT NULL,
    current_model_version_id TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    updated_by_actor_id TEXT NOT NULL,
    PRIMARY KEY (tenant_id, model_family_id, environment),
    CONSTRAINT fk_portal_model_slot_version
        FOREIGN KEY (tenant_id, current_model_version_id)
        REFERENCES portal_model_versions (tenant_id, model_version_id)
        ON DELETE RESTRICT
);

CREATE INDEX ix_portal_model_slots_tenant_model
    ON portal_model_promotion_slots (tenant_id, current_model_version_id);

CREATE TABLE portal_model_promotion_history (
    transition_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    model_family_id TEXT NOT NULL,
    environment TEXT NOT NULL,
    from_model_version_id TEXT NULL,
    to_model_version_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX ix_portal_model_promotion_history_slot
    ON portal_model_promotion_history (
        tenant_id,
        model_family_id,
        environment,
        occurred_at
    );

CREATE INDEX ix_portal_model_promotion_history_target
    ON portal_model_promotion_history (tenant_id, to_model_version_id);

COMMIT;
