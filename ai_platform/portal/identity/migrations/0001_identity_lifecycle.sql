BEGIN;

CREATE TABLE portal_identity_principals (
    principal_id TEXT PRIMARY KEY,
    issuer TEXT NOT NULL,
    subject TEXT NOT NULL,
    display_name TEXT NOT NULL,
    email TEXT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_portal_identity_issuer_subject UNIQUE (issuer, subject)
);

CREATE INDEX ix_portal_identity_principal_status
    ON portal_identity_principals (status);

CREATE TABLE portal_tenant_memberships (
    membership_id TEXT PRIMARY KEY,
    principal_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    roles_json TEXT NOT NULL,
    status TEXT NOT NULL,
    membership_version INTEGER NOT NULL CHECK (membership_version > 0),
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_portal_membership_principal_tenant UNIQUE (principal_id, tenant_id),
    CONSTRAINT fk_portal_membership_principal
        FOREIGN KEY (principal_id)
        REFERENCES portal_identity_principals (principal_id)
        ON DELETE RESTRICT
);

CREATE INDEX ix_portal_membership_tenant_status
    ON portal_tenant_memberships (tenant_id, status);

CREATE INDEX ix_portal_membership_principal
    ON portal_tenant_memberships (principal_id);

CREATE TABLE portal_identity_sessions (
    session_id_hash TEXT PRIMARY KEY,
    csrf_token_hash TEXT NOT NULL,
    principal_id TEXT NOT NULL,
    membership_id TEXT NOT NULL,
    membership_version INTEGER NOT NULL CHECK (membership_version > 0),
    idp_session_id TEXT NULL,
    authentication_time TIMESTAMPTZ NOT NULL,
    mfa_satisfied BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    idle_expires_at TIMESTAMPTZ NOT NULL,
    absolute_expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ NULL,
    revocation_reason TEXT NULL,
    CONSTRAINT fk_portal_session_principal
        FOREIGN KEY (principal_id)
        REFERENCES portal_identity_principals (principal_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_portal_session_membership
        FOREIGN KEY (membership_id)
        REFERENCES portal_tenant_memberships (membership_id)
        ON DELETE RESTRICT
);

CREATE INDEX ix_portal_session_principal_active
    ON portal_identity_sessions (principal_id, revoked_at);

CREATE INDEX ix_portal_session_membership_active
    ON portal_identity_sessions (membership_id, revoked_at);

CREATE INDEX ix_portal_session_idp_sid
    ON portal_identity_sessions (idp_session_id);

CREATE TABLE portal_oidc_login_flows (
    state_hash TEXT PRIMARY KEY,
    nonce TEXT NOT NULL,
    verifier_ciphertext TEXT NOT NULL,
    requested_tenant_id TEXT NULL,
    return_to TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ NULL
);

CREATE INDEX ix_portal_oidc_flow_expiry
    ON portal_oidc_login_flows (expires_at, consumed_at);

CREATE TABLE portal_session_revocations (
    revocation_id TEXT PRIMARY KEY,
    principal_id TEXT NOT NULL,
    session_id_hash TEXT NULL,
    idp_session_id TEXT NULL,
    actor_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    correlation_id TEXT NULL
);

CREATE INDEX ix_portal_revocation_principal_time
    ON portal_session_revocations (principal_id, occurred_at);

CREATE TABLE portal_identity_audit_events (
    event_id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    principal_id TEXT NULL,
    tenant_id TEXT NULL,
    membership_id TEXT NULL,
    result TEXT NOT NULL,
    reason TEXT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    correlation_id TEXT NULL
);

CREATE INDEX ix_portal_identity_audit_principal_time
    ON portal_identity_audit_events (principal_id, occurred_at);

CREATE INDEX ix_portal_identity_audit_tenant_time
    ON portal_identity_audit_events (tenant_id, occurred_at);

COMMIT;
