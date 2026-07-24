CREATE TABLE portal_operational_trades (
    tenant_id VARCHAR(255) NOT NULL,
    trade_id VARCHAR(255) NOT NULL,
    bot_id VARCHAR(255) NOT NULL,
    source_runtime_id VARCHAR(255) NOT NULL,
    opened_at TIMESTAMP WITH TIME ZONE NOT NULL,
    trade_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, trade_id)
);

CREATE INDEX ix_portal_operational_trades_tenant_bot
    ON portal_operational_trades (tenant_id, bot_id, opened_at);

CREATE TABLE portal_operational_source_status (
    tenant_id VARCHAR(255) NOT NULL,
    bot_id VARCHAR(255) NOT NULL,
    source_runtime_id VARCHAR(255) NOT NULL,
    kind VARCHAR(64) NOT NULL,
    observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, bot_id, source_runtime_id, kind)
);

CREATE INDEX ix_portal_operational_source_status_tenant_runtime
    ON portal_operational_source_status (tenant_id, source_runtime_id, observed_at);
