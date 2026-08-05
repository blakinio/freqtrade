BEGIN;

CREATE TABLE portal_oidc_logout_replays (
    replay_key_hash VARCHAR(64) PRIMARY KEY,
    issuer VARCHAR(1024) NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    jti VARCHAR(255) NOT NULL,
    request_fingerprint VARCHAR(64) NOT NULL,
    token_type VARCHAR(32) NOT NULL,
    signing_key_id VARCHAR(255) NOT NULL,
    signing_algorithm VARCHAR(32) NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL,
    token_expires_at TIMESTAMPTZ NOT NULL,
    retention_until TIMESTAMPTZ NOT NULL,
    status VARCHAR(32) NOT NULL,
    revoked_sessions INTEGER NULL,
    processed_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NULL,
    CONSTRAINT ck_portal_oidc_logout_replay_status
        CHECK (status IN ('processing', 'completed')),
    CONSTRAINT ck_portal_oidc_logout_replay_revoked_sessions
        CHECK (revoked_sessions IS NULL OR revoked_sessions >= 0),
    CONSTRAINT ck_portal_oidc_logout_replay_token_window
        CHECK (token_expires_at > issued_at),
    CONSTRAINT ck_portal_oidc_logout_replay_retention_window
        CHECK (retention_until > token_expires_at),
    CONSTRAINT ck_portal_oidc_logout_replay_terminal_result
        CHECK (
            (
                status = 'processing'
                AND revoked_sessions IS NULL
                AND processed_at IS NULL
                AND completed_at IS NULL
            )
            OR
            (
                status = 'completed'
                AND revoked_sessions IS NOT NULL
                AND processed_at IS NOT NULL
                AND completed_at IS NOT NULL
            )
        )
);

CREATE INDEX ix_portal_oidc_logout_replay_created
    ON portal_oidc_logout_replays (created_at);

CREATE INDEX ix_portal_oidc_logout_replay_retention
    ON portal_oidc_logout_replays (retention_until, status);

COMMIT;
