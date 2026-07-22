from ai_platform.portal.observability.redaction import REDACTED, redact_sensitive


def test_redaction_recursively_covers_secret_token_password_and_cookie_aliases() -> None:
    payload = {
        "safe": "visible",
        "api_key": "key-value",
        "nested": {
            "clientSecret": "client-value",
            "items": [
                {"access_token": "access-value"},
                {"Set-Cookie": "session=value"},
                {"private_key": "private-value"},
            ],
        },
    }

    redacted = redact_sensitive(payload)

    assert redacted["safe"] == "visible"
    assert redacted["api_key"] == REDACTED
    assert redacted["nested"]["clientSecret"] == REDACTED
    assert redacted["nested"]["items"][0]["access_token"] == REDACTED
    assert redacted["nested"]["items"][1]["Set-Cookie"] == REDACTED
    assert redacted["nested"]["items"][2]["private_key"] == REDACTED
    assert payload["api_key"] == "key-value"
