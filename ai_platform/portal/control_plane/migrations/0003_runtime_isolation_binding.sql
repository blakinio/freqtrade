-- ADR-020 runtime-generation isolation/TCB identity binding.
--
-- Historical RuntimeGeneration rows cannot be assigned these values safely: the
-- exact resolved plan, Gateway artifact/contract and egress-policy identities
-- must have been known before execution. The authoritative Python migrator
-- therefore refuses this revision when portal_runtime_generations contains rows.

ALTER TABLE portal_runtime_generations
    ADD COLUMN isolation_plan_digest VARCHAR(64) NOT NULL;
ALTER TABLE portal_runtime_generations
    ADD COLUMN gateway_artifact_digest VARCHAR(64) NOT NULL;
ALTER TABLE portal_runtime_generations
    ADD COLUMN gateway_contract_digest VARCHAR(64) NOT NULL;
ALTER TABLE portal_runtime_generations
    ADD COLUMN market_data_egress_policy_version VARCHAR(255) NOT NULL;
ALTER TABLE portal_runtime_generations
    ADD COLUMN market_data_egress_policy_digest VARCHAR(64) NOT NULL;
