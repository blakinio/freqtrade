CREATE TABLE portal_signal_events (
    tenant_id VARCHAR(255) NOT NULL,
    signal_id VARCHAR(36) NOT NULL,
    bot_id VARCHAR(255) NOT NULL,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    signal_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, signal_id)
);

CREATE INDEX ix_portal_signal_events_tenant_time
    ON portal_signal_events (tenant_id, occurred_at, signal_id);
CREATE INDEX ix_portal_signal_events_tenant_bot
    ON portal_signal_events (tenant_id, bot_id, occurred_at);

CREATE TABLE portal_grid_bot_configs (
    tenant_id VARCHAR(255) NOT NULL,
    grid_config_id VARCHAR(36) NOT NULL,
    bot_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    config_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, grid_config_id)
);

CREATE INDEX ix_portal_grid_bot_configs_tenant_bot
    ON portal_grid_bot_configs (tenant_id, bot_id, created_at);

CREATE TABLE portal_notification_preferences (
    tenant_id VARCHAR(255) NOT NULL,
    actor_id VARCHAR(255) NOT NULL,
    in_app_enabled BOOLEAN NOT NULL,
    signal_events BOOLEAN NOT NULL,
    risk_events BOOLEAN NOT NULL,
    execution_events BOOLEAN NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    preference_json TEXT NOT NULL,
    revision INTEGER NOT NULL,
    PRIMARY KEY (tenant_id, actor_id)
);
