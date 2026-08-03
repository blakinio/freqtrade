BEGIN;

-- Preserve existing data and fail closed before narrowing any text column.
DO $$
DECLARE
    target record;
    oversized boolean;
BEGIN
    FOR target IN
        SELECT *
        FROM (VALUES
            ('portal_audit_events', 'action', 128),
            ('portal_audit_events', 'actor_id', 255),
            ('portal_audit_events', 'audit_id', 36),
            ('portal_audit_events', 'resource_id', 255),
            ('portal_audit_events', 'resource_type', 255),
            ('portal_audit_events', 'result', 32),
            ('portal_audit_events', 'tenant_id', 255),
            ('portal_bot_config_revisions', 'bot_id', 255),
            ('portal_bot_config_revisions', 'created_by_actor_id', 255),
            ('portal_bot_config_revisions', 'revision_id', 255),
            ('portal_bot_config_revisions', 'tenant_id', 255),
            ('portal_bots', 'bot_id', 255),
            ('portal_bots', 'desired_state', 32),
            ('portal_bots', 'name', 255),
            ('portal_bots', 'observed_state', 32),
            ('portal_bots', 'tenant_id', 255),
            ('portal_event_inbox', 'consumer_name', 255),
            ('portal_event_inbox', 'correlation_id', 36),
            ('portal_event_inbox', 'event_id', 36),
            ('portal_event_inbox', 'event_type', 128),
            ('portal_event_inbox', 'tenant_id', 255),
            ('portal_identity_audit_events', 'action', 128),
            ('portal_identity_audit_events', 'actor_id', 255),
            ('portal_identity_audit_events', 'correlation_id', 36),
            ('portal_identity_audit_events', 'event_id', 36),
            ('portal_identity_audit_events', 'membership_id', 36),
            ('portal_identity_audit_events', 'principal_id', 36),
            ('portal_identity_audit_events', 'reason', 255),
            ('portal_identity_audit_events', 'result', 32),
            ('portal_identity_audit_events', 'tenant_id', 255),
            ('portal_identity_principals', 'display_name', 255),
            ('portal_identity_principals', 'email', 320),
            ('portal_identity_principals', 'issuer', 1024),
            ('portal_identity_principals', 'principal_id', 36),
            ('portal_identity_principals', 'status', 32),
            ('portal_identity_principals', 'subject', 512),
            ('portal_identity_sessions', 'csrf_token_hash', 64),
            ('portal_identity_sessions', 'idp_session_id', 512),
            ('portal_identity_sessions', 'membership_id', 36),
            ('portal_identity_sessions', 'principal_id', 36),
            ('portal_identity_sessions', 'revocation_reason', 255),
            ('portal_identity_sessions', 'session_id_hash', 64),
            ('portal_model_promotion_history', 'action', 32),
            ('portal_model_promotion_history', 'actor_id', 255),
            ('portal_model_promotion_history', 'environment', 32),
            ('portal_model_promotion_history', 'from_model_version_id', 255),
            ('portal_model_promotion_history', 'model_family_id', 255),
            ('portal_model_promotion_history', 'tenant_id', 255),
            ('portal_model_promotion_history', 'to_model_version_id', 255),
            ('portal_model_promotion_history', 'transition_id', 36),
            ('portal_model_promotion_slots', 'current_model_version_id', 255),
            ('portal_model_promotion_slots', 'environment', 32),
            ('portal_model_promotion_slots', 'model_family_id', 255),
            ('portal_model_promotion_slots', 'tenant_id', 255),
            ('portal_model_promotion_slots', 'updated_by_actor_id', 255),
            ('portal_model_versions', 'model_family_id', 255),
            ('portal_model_versions', 'model_version_id', 255),
            ('portal_model_versions', 'registered_by_actor_id', 255),
            ('portal_model_versions', 'tenant_id', 255),
            ('portal_oidc_login_flows', 'nonce', 255),
            ('portal_oidc_login_flows', 'requested_tenant_id', 255),
            ('portal_oidc_login_flows', 'return_to', 2048),
            ('portal_oidc_login_flows', 'state_hash', 64),
            ('portal_outbox_events', 'aggregate_id', 255),
            ('portal_outbox_events', 'aggregate_type', 255),
            ('portal_outbox_events', 'event_id', 36),
            ('portal_outbox_events', 'event_type', 128),
            ('portal_outbox_events', 'tenant_id', 255),
            ('portal_session_revocations', 'actor_id', 255),
            ('portal_session_revocations', 'correlation_id', 36),
            ('portal_session_revocations', 'idp_session_id', 512),
            ('portal_session_revocations', 'principal_id', 36),
            ('portal_session_revocations', 'reason', 255),
            ('portal_session_revocations', 'revocation_id', 36),
            ('portal_session_revocations', 'session_id_hash', 64),
            ('portal_tenant_memberships', 'membership_id', 36),
            ('portal_tenant_memberships', 'principal_id', 36),
            ('portal_tenant_memberships', 'status', 32),
            ('portal_tenant_memberships', 'tenant_id', 255)
        ) AS values_to_align(table_name, column_name, max_length)
    LOOP
        EXECUTE format(
            'SELECT EXISTS (SELECT 1 FROM %%I WHERE char_length(%%I) > $1)',
            target.table_name,
            target.column_name
        )
        INTO oversized
        USING target.max_length;

        IF oversized THEN
            RAISE EXCEPTION 'schema alignment blocked: %%.%% exceeds VARCHAR(%%)',
                target.table_name, target.column_name, target.max_length;
        END IF;

        EXECUTE format(
            'ALTER TABLE %%I ALTER COLUMN %%I TYPE VARCHAR(%%s)',
            target.table_name,
            target.column_name,
            target.max_length
        );
    END LOOP;
END
$$;

ALTER TABLE portal_execution_submissions
    ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC';

ALTER TABLE portal_execution_submissions
    ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC';

COMMIT;
