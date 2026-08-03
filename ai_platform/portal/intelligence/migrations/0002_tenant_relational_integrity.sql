BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM portal_decision_snapshots snapshot
        LEFT JOIN portal_bots bot
          ON bot.tenant_id = snapshot.tenant_id
         AND bot.bot_id = snapshot.bot_id
        WHERE bot.bot_id IS NULL
    ) THEN
        RAISE EXCEPTION 'portal_decision_snapshots contains an unknown tenant-scoped bot reference';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM portal_decision_snapshots snapshot
        LEFT JOIN portal_trade_intents intent
          ON intent.tenant_id = snapshot.tenant_id
         AND intent.trade_intent_id = snapshot.trade_intent_id
        WHERE intent.trade_intent_id IS NULL
    ) THEN
        RAISE EXCEPTION 'portal_decision_snapshots contains an unknown tenant-scoped trade intent reference';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM portal_trade_outcomes outcome
        LEFT JOIN portal_bots bot
          ON bot.tenant_id = outcome.tenant_id
         AND bot.bot_id = outcome.bot_id
        WHERE bot.bot_id IS NULL
    ) THEN
        RAISE EXCEPTION 'portal_trade_outcomes contains an unknown tenant-scoped bot reference';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM portal_trade_analyses analysis
        LEFT JOIN portal_decision_snapshots snapshot
          ON snapshot.tenant_id = analysis.tenant_id
         AND snapshot.snapshot_id = analysis.snapshot_id
        WHERE snapshot.snapshot_id IS NULL
    ) THEN
        RAISE EXCEPTION 'portal_trade_analyses contains an unknown tenant-scoped snapshot reference';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM portal_trade_analyses analysis
        LEFT JOIN portal_trade_outcomes outcome
          ON outcome.tenant_id = analysis.tenant_id
         AND outcome.outcome_id = analysis.outcome_id
        WHERE outcome.outcome_id IS NULL
    ) THEN
        RAISE EXCEPTION 'portal_trade_analyses contains an unknown tenant-scoped outcome reference';
    END IF;
END
$$;

ALTER TABLE portal_decision_snapshots
    DROP CONSTRAINT IF EXISTS portal_decision_snapshots_trade_intent_id_key;

ALTER TABLE portal_decision_snapshots
    ADD CONSTRAINT uq_portal_decision_snapshot_tenant_intent
    UNIQUE (tenant_id, trade_intent_id);

ALTER TABLE portal_decision_snapshots
    ADD CONSTRAINT fk_portal_decision_snapshot_bot
    FOREIGN KEY (tenant_id, bot_id)
    REFERENCES portal_bots (tenant_id, bot_id)
    ON DELETE RESTRICT;

ALTER TABLE portal_decision_snapshots
    ADD CONSTRAINT fk_portal_decision_snapshot_intent
    FOREIGN KEY (tenant_id, trade_intent_id)
    REFERENCES portal_trade_intents (tenant_id, trade_intent_id)
    ON DELETE RESTRICT;

ALTER TABLE portal_trade_outcomes
    ADD CONSTRAINT fk_portal_trade_outcome_bot
    FOREIGN KEY (tenant_id, bot_id)
    REFERENCES portal_bots (tenant_id, bot_id)
    ON DELETE RESTRICT;

ALTER TABLE portal_trade_analyses
    ADD CONSTRAINT fk_portal_trade_analysis_snapshot
    FOREIGN KEY (tenant_id, snapshot_id)
    REFERENCES portal_decision_snapshots (tenant_id, snapshot_id)
    ON DELETE RESTRICT;

ALTER TABLE portal_trade_analyses
    ADD CONSTRAINT fk_portal_trade_analysis_outcome
    FOREIGN KEY (tenant_id, outcome_id)
    REFERENCES portal_trade_outcomes (tenant_id, outcome_id)
    ON DELETE RESTRICT;

DROP INDEX IF EXISTS ix_portal_decision_snapshots_bot_id;
DROP INDEX IF EXISTS ix_portal_decision_snapshots_decision_at;
DROP INDEX IF EXISTS ix_portal_trade_outcomes_trade_id;
DROP INDEX IF EXISTS ix_portal_trade_outcomes_bot_id;
DROP INDEX IF EXISTS ix_portal_trade_outcomes_closed_at;
DROP INDEX IF EXISTS ix_portal_trade_analyses_snapshot_id;
DROP INDEX IF EXISTS ix_portal_trade_analyses_outcome_id;
DROP INDEX IF EXISTS ix_portal_trade_analyses_diagnosis_code;
DROP INDEX IF EXISTS ix_portal_trade_analyses_created_at;

CREATE INDEX ix_portal_decision_snapshots_tenant_bot
    ON portal_decision_snapshots (tenant_id, bot_id);
CREATE INDEX ix_portal_decision_snapshots_tenant_decision_at
    ON portal_decision_snapshots (tenant_id, decision_at);
CREATE INDEX ix_portal_trade_outcomes_tenant_trade
    ON portal_trade_outcomes (tenant_id, trade_id);
CREATE INDEX ix_portal_trade_outcomes_tenant_bot
    ON portal_trade_outcomes (tenant_id, bot_id);
CREATE INDEX ix_portal_trade_outcomes_tenant_closed_at
    ON portal_trade_outcomes (tenant_id, closed_at);
CREATE INDEX ix_portal_trade_analyses_tenant_snapshot
    ON portal_trade_analyses (tenant_id, snapshot_id);
CREATE INDEX ix_portal_trade_analyses_tenant_outcome
    ON portal_trade_analyses (tenant_id, outcome_id);
CREATE INDEX ix_portal_trade_analyses_tenant_diagnosis
    ON portal_trade_analyses (tenant_id, diagnosis_code);
CREATE INDEX ix_portal_trade_analyses_tenant_created_at
    ON portal_trade_analyses (tenant_id, created_at);

COMMIT;
