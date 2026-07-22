CREATE TABLE IF NOT EXISTS portal_learning_hypotheses (
    tenant_id VARCHAR(255) NOT NULL,
    hypothesis_id VARCHAR(36) NOT NULL,
    source_insight_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    hypothesis_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, hypothesis_id)
);
CREATE INDEX IF NOT EXISTS ix_portal_learning_hypotheses_source_insight_id
    ON portal_learning_hypotheses (source_insight_id);

CREATE TABLE IF NOT EXISTS portal_learning_experiments (
    tenant_id VARCHAR(255) NOT NULL,
    experiment_id VARCHAR(36) NOT NULL,
    hypothesis_id VARCHAR(36) NOT NULL,
    outcome VARCHAR(32) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    experiment_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, experiment_id)
);
CREATE INDEX IF NOT EXISTS ix_portal_learning_experiments_hypothesis_id
    ON portal_learning_experiments (hypothesis_id);
CREATE INDEX IF NOT EXISTS ix_portal_learning_experiments_outcome
    ON portal_learning_experiments (outcome);

CREATE TABLE IF NOT EXISTS portal_learning_candidates (
    tenant_id VARCHAR(255) NOT NULL,
    candidate_id VARCHAR(36) NOT NULL,
    experiment_id VARCHAR(36) NOT NULL,
    candidate_model_version_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    candidate_json TEXT NOT NULL,
    PRIMARY KEY (tenant_id, candidate_id)
);
CREATE INDEX IF NOT EXISTS ix_portal_learning_candidates_experiment_id
    ON portal_learning_candidates (experiment_id);
CREATE INDEX IF NOT EXISTS ix_portal_learning_candidates_model_version_id
    ON portal_learning_candidates (candidate_model_version_id);
