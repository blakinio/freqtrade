CREATE TABLE portal_risk_policies (
    tenant_id VARCHAR(255) NOT NULL,
    risk_policy_version_id VARCHAR(255) NOT NULL,
    policy_hash VARCHAR(64) NOT NULL,
    definition_json TEXT NOT NULL,
    created_by_actor_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (tenant_id, risk_policy_version_id)
);

CREATE INDEX ix_portal_risk_policy_tenant
    ON portal_risk_policies (tenant_id);

CREATE TABLE portal_risk_kill_switches (
    tenant_id VARCHAR(255) NOT NULL,
    environment VARCHAR(32) NOT NULL,
    active BOOLEAN NOT NULL,
    reason_code VARCHAR(255),
    updated_by_actor_id VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (tenant_id, environment)
);

CREATE TABLE portal_trade_intents (
    tenant_id VARCHAR(255) NOT NULL,
    trade_intent_id VARCHAR(36) NOT NULL,
    bot_id VARCHAR(255) NOT NULL,
    intent_json TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (tenant_id, trade_intent_id)
);

CREATE INDEX ix_portal_trade_intents_tenant_bot
    ON portal_trade_intents (tenant_id, bot_id, created_at);

CREATE TABLE portal_risk_decisions (
    tenant_id VARCHAR(255) NOT NULL,
    risk_decision_id VARCHAR(36) NOT NULL,
    trade_intent_id VARCHAR(36) NOT NULL,
    decision_json TEXT NOT NULL,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (tenant_id, risk_decision_id),
    CONSTRAINT fk_portal_risk_decision_intent
        FOREIGN KEY (tenant_id, trade_intent_id)
        REFERENCES portal_trade_intents (tenant_id, trade_intent_id)
        ON DELETE RESTRICT
);

CREATE INDEX ix_portal_risk_decisions_tenant_intent
    ON portal_risk_decisions (tenant_id, trade_intent_id, occurred_at);
