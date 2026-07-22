CREATE TABLE IF NOT EXISTS portal_decision_snapshots (
    tenant_id VARCHAR(255) NOT NULL,
    snapshot_id VARCHAR(36) NOT NULL,
    bot_id VARCHAR(255) NOT NULL,
    trade_intent_id VARCHAR(36) NOT NULL UNIQUE,
    decision_at TIMESTAMP WITH TIME ZONE NOT NULL,
    snapshot_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, snapshot_id)
);

CREATE INDEX IF NOT EXISTS ix_portal_decision_snapshots_bot_id
    ON portal_decision_snapshots (bot_id);
CREATE INDEX IF NOT EXISTS ix_portal_decision_snapshots_decision_at
    ON portal_decision_snapshots (decision_at);

CREATE TABLE IF NOT EXISTS portal_trade_outcomes (
    tenant_id VARCHAR(255) NOT NULL,
    outcome_id VARCHAR(36) NOT NULL,
    trade_id VARCHAR(255) NOT NULL,
    bot_id VARCHAR(255) NOT NULL,
    closed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    outcome_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, outcome_id)
);

CREATE INDEX IF NOT EXISTS ix_portal_trade_outcomes_trade_id
    ON portal_trade_outcomes (trade_id);
CREATE INDEX IF NOT EXISTS ix_portal_trade_outcomes_bot_id
    ON portal_trade_outcomes (bot_id);
CREATE INDEX IF NOT EXISTS ix_portal_trade_outcomes_closed_at
    ON portal_trade_outcomes (closed_at);

CREATE TABLE IF NOT EXISTS portal_trade_analyses (
    tenant_id VARCHAR(255) NOT NULL,
    analysis_id VARCHAR(36) NOT NULL,
    snapshot_id VARCHAR(36) NOT NULL,
    outcome_id VARCHAR(36) NOT NULL,
    diagnosis_code VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    analysis_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, analysis_id)
);

CREATE INDEX IF NOT EXISTS ix_portal_trade_analyses_snapshot_id
    ON portal_trade_analyses (snapshot_id);
CREATE INDEX IF NOT EXISTS ix_portal_trade_analyses_outcome_id
    ON portal_trade_analyses (outcome_id);
CREATE INDEX IF NOT EXISTS ix_portal_trade_analyses_diagnosis_code
    ON portal_trade_analyses (diagnosis_code);
CREATE INDEX IF NOT EXISTS ix_portal_trade_analyses_created_at
    ON portal_trade_analyses (created_at);
