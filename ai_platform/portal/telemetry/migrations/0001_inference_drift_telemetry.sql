CREATE TABLE portal_inference_telemetry_windows (
    tenant_id VARCHAR(255) NOT NULL,
    telemetry_id VARCHAR(36) NOT NULL,
    model_version_id VARCHAR(255) NOT NULL,
    feature_schema_version_id VARCHAR(255) NOT NULL,
    bot_id VARCHAR(255) NOT NULL,
    bot_config_revision INTEGER NOT NULL,
    bot_config_revision_id VARCHAR(255) NOT NULL,
    runtime_id VARCHAR(255) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL,
    window_start_at TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end_at TIMESTAMP WITH TIME ZONE NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    telemetry_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, telemetry_id)
);

CREATE INDEX ix_portal_inference_windows_tenant_model_role
    ON portal_inference_telemetry_windows
    (tenant_id, model_version_id, role, window_end_at);

CREATE INDEX ix_portal_inference_windows_tenant_runtime
    ON portal_inference_telemetry_windows
    (tenant_id, runtime_id, bot_config_revision_id, window_end_at);

CREATE TABLE portal_inference_telemetry_source_status (
    tenant_id VARCHAR(255) NOT NULL,
    model_version_id VARCHAR(255) NOT NULL,
    feature_schema_version_id VARCHAR(255) NOT NULL,
    bot_id VARCHAR(255) NOT NULL,
    bot_config_revision_id VARCHAR(255) NOT NULL,
    runtime_id VARCHAR(255) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    checked_at TIMESTAMP WITH TIME ZONE NOT NULL,
    availability VARCHAR(32) NOT NULL,
    reason_code VARCHAR(255) NOT NULL,
    status_json TEXT NOT NULL,
    PRIMARY KEY (
        tenant_id,
        model_version_id,
        feature_schema_version_id,
        bot_id,
        bot_config_revision_id,
        runtime_id,
        source_id
    )
);

CREATE INDEX ix_portal_inference_source_status_tenant_model
    ON portal_inference_telemetry_source_status
    (tenant_id, model_version_id, checked_at);

CREATE TABLE portal_inference_drift_assessments (
    tenant_id VARCHAR(255) NOT NULL,
    assessment_id VARCHAR(64) NOT NULL,
    model_version_id VARCHAR(255) NOT NULL,
    feature_schema_version_id VARCHAR(255) NOT NULL,
    bot_id VARCHAR(255) NOT NULL,
    bot_config_revision_id VARCHAR(255) NOT NULL,
    runtime_id VARCHAR(255) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    reference_telemetry_id VARCHAR(36) NOT NULL,
    observation_telemetry_id VARCHAR(36) NOT NULL,
    observation_window_end_at TIMESTAMP WITH TIME ZONE NOT NULL,
    assessed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(64) NOT NULL,
    assessment_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, assessment_id)
);

CREATE INDEX ix_portal_inference_assessments_tenant_model
    ON portal_inference_drift_assessments
    (tenant_id, model_version_id, observation_window_end_at);

CREATE INDEX ix_portal_inference_assessments_tenant_runtime
    ON portal_inference_drift_assessments
    (tenant_id, runtime_id, bot_config_revision_id, observation_window_end_at);
