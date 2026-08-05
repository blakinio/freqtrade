BEGIN;

CREATE TABLE portal_oidc_logout_replays (
    replay_key_hash VARCHAR(64) PRIMARY KEY,
    issuer VARCHAR(1024) NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    jti VARCHAR(255) NOT NULL,
    request_fingerprint VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    revoked_sessions INTEGER NULL,
    processed_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ NULL,
    CONSTRAINT ck_portal_oidc_logout_replay_status
        CHECK (status IN ('processing', 'completed')),
    CONSTRAINT ck_portal_oidc_logout_replay_revoked_sessions
        CHECK (revoked_sessions IS NULL OR revoked_sessions >= 0),
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

COMMIT;
