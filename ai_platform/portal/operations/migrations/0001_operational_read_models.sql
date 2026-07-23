CREATE TABLE portal_operational_orders (
    tenant_id VARCHAR(255) NOT NULL,
    order_id VARCHAR(255) NOT NULL,
    bot_id VARCHAR(255) NOT NULL,
    source_runtime_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    order_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, order_id)
);

CREATE INDEX ix_portal_operational_orders_tenant_bot
    ON portal_operational_orders (tenant_id, bot_id, created_at);

CREATE TABLE portal_operational_positions (
    tenant_id VARCHAR(255) NOT NULL,
    position_id VARCHAR(255) NOT NULL,
    bot_id VARCHAR(255) NOT NULL,
    source_runtime_id VARCHAR(255) NOT NULL,
    opened_at TIMESTAMP WITH TIME ZONE NOT NULL,
    position_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, position_id)
);

CREATE INDEX ix_portal_operational_positions_tenant_bot
    ON portal_operational_positions (tenant_id, bot_id, opened_at);
