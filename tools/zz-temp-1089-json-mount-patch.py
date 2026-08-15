from __future__ import annotations

from pathlib import Path


CODE_PATH = Path("deploy/synology/portal-oidc/deploy_entrypoint.py")
TESTS_PATH = Path("tests/ai_platform/portal/deployment/test_portal_oidc_deploy_entrypoint.py")
CONTROL_PATH = Path(
    "tests/ai_platform/portal/deployment/"
    "test_portal_oidc_market_evidence_host_mount_whitespace.py"
)


def patch_entrypoint() -> None:
    source = CODE_PATH.read_text(encoding="utf-8")
    if "import json\n" not in source:
        source = source.replace("import importlib.util\n", "import importlib.util\nimport json\n", 1)

    old_format = '''RUNNER_STATE_INSPECT_FORMAT = (\n    "{{.State.Running}}|"\n    '{{index .Config.Labels "com.docker.compose.project"}}|'\n    '{{index .Config.Labels "com.docker.compose.service"}}{{println}}'\n    "{{range .Mounts}}"\n    f'{{{{if eq .Destination "{RUNNER_STATE_DESTINATION}"}}}}'\n    "{{.Type}}|{{.Source}}{{println}}"\n    "{{end}}{{end}}"\n)\n'''
    new_format = '''RUNNER_STATE_INSPECT_FORMAT = (\n    "{{json .State.Running}}{{println}}"\n    '{{json (index .Config.Labels "com.docker.compose.project")}}{{println}}'\n    '{{json (index .Config.Labels "com.docker.compose.service")}}{{println}}'\n    "{{range .Mounts}}"\n    f'{{{{if eq .Destination "{RUNNER_STATE_DESTINATION}"}}}}'\n    "{{json .}}{{println}}"\n    "{{end}}{{end}}"\n)\n'''
    if source.count(old_format) != 1:
        raise SystemExit("runner inspect format replacement mismatch")
    source = source.replace(old_format, new_format)

    old_resolver = '''    lines = [line for line in result.stdout.split("\\n") if line]\n    if not lines:\n        raise deploy.DeploymentError("Synology staging runner identity is invalid")\n\n    running, state_separator, identity = lines[0].partition("|")\n    project, project_separator, service = identity.partition("|")\n    if (\n        state_separator != "|"\n        or project_separator != "|"\n        or running != "true"\n        or project != RUNNER_COMPOSE_PROJECT\n        or service != RUNNER_COMPOSE_SERVICE\n    ):\n        raise deploy.DeploymentError("Synology staging runner identity is invalid")\n\n    matches = lines[1:]\n    if len(matches) != 1:\n        raise deploy.DeploymentError(\n            "Synology runner must expose exactly one canonical staging-state host bind"\n        )\n    mount_type, separator, source = matches[0].partition("|")\n    source_path = Path(source)\n    if (\n        separator != "|"\n        or mount_type != "bind"\n        or re.fullmatch(r"/volume1/docker/[A-Za-z0-9._/-]+", source) is None\n        or not source_path.is_absolute()\n        or source != source_path.as_posix()\n        or ".." in source_path.parts\n    ):\n        raise deploy.DeploymentError("Synology runner staging-state host bind is invalid")\n    return source_path / MARKET_EVIDENCE_STATE_DIR\n'''
    new_resolver = '''    records = result.stdout.splitlines()\n    if len(records) < 3:\n        raise deploy.DeploymentError("Synology staging runner identity is invalid")\n    try:\n        running = json.loads(records[0])\n        project = json.loads(records[1])\n        service = json.loads(records[2])\n    except (json.JSONDecodeError, TypeError):\n        raise deploy.DeploymentError("Synology staging runner identity is invalid") from None\n    if (\n        running is not True\n        or project != RUNNER_COMPOSE_PROJECT\n        or service != RUNNER_COMPOSE_SERVICE\n    ):\n        raise deploy.DeploymentError("Synology staging runner identity is invalid")\n\n    mount_records = records[3:]\n    if len(mount_records) != 1:\n        raise deploy.DeploymentError(\n            "Synology runner must expose exactly one canonical staging-state host bind"\n        )\n    try:\n        mount = json.loads(mount_records[0])\n    except (json.JSONDecodeError, TypeError):\n        raise deploy.DeploymentError("Synology runner staging-state host bind is invalid") from None\n    if not isinstance(mount, dict):\n        raise deploy.DeploymentError("Synology runner staging-state host bind is invalid")\n    mount_type = mount.get("Type")\n    destination = mount.get("Destination")\n    source = mount.get("Source")\n    if not isinstance(source, str):\n        raise deploy.DeploymentError("Synology runner staging-state host bind is invalid")\n    source_path = Path(source)\n    if (\n        mount_type != "bind"\n        or destination != RUNNER_STATE_DESTINATION\n        or re.fullmatch(r"/volume1/docker/[A-Za-z0-9._/-]+", source) is None\n        or not source_path.is_absolute()\n        or source != source_path.as_posix()\n        or ".." in source_path.parts\n    ):\n        raise deploy.DeploymentError("Synology runner staging-state host bind is invalid")\n    return source_path / MARKET_EVIDENCE_STATE_DIR\n'''
    if source.count(old_resolver) != 1:
        raise SystemExit("runner resolver replacement mismatch")
    CODE_PATH.write_text(source.replace(old_resolver, new_resolver), encoding="utf-8")


def patch_entrypoint_tests() -> None:
    tests = TESTS_PATH.read_text(encoding="utf-8")
    if "import json\n" not in tests:
        tests = tests.replace("import importlib.util\n", "import importlib.util\nimport json\n", 1)
    start = tests.index("def test_market_evidence_host_root_follows_exact_runner_state_bind")
    replacement = r'''def _runner_inspect_payload(
    *,
    running: bool = True,
    project: str = "freqtrade-deploy-runner",
    service: str = "runner",
    mounts: list[dict[str, object]] | None = None,
) -> str:
    records = [json.dumps(running), json.dumps(project), json.dumps(service)]
    records.extend(json.dumps(mount, separators=(",", ":")) for mount in (mounts or []))
    return "\n".join(records) + "\n"


def _runner_mount(source: str, *, mount_type: str = "bind") -> dict[str, object]:
    return {
        "Type": mount_type,
        "Source": source,
        "Destination": entrypoint.RUNNER_STATE_DESTINATION,
        "Mode": "",
        "RW": True,
        "Propagation": "rprivate",
    }


def test_market_evidence_host_root_follows_exact_runner_state_bind() -> None:
    calls: list[tuple[list[str], bool]] = []

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((command, bool(kwargs.get("sensitive"))))
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=_runner_inspect_payload(
                mounts=[_runner_mount("/volume1/docker/freqtrade/state")]
            ),
            stderr="",
        )

    deploy = SimpleNamespace(_run=run, DeploymentError=RuntimeError)

    assert entrypoint._resolve_market_evidence_host_root(deploy) == Path(
        "/volume1/docker/freqtrade/state/wickhunter-production-market-evidence"
    )
    assert calls == [
        (
            [
                "docker",
                "inspect",
                "--format",
                entrypoint.RUNNER_STATE_INSPECT_FORMAT,
                entrypoint.RUNNER_CONTAINER,
            ],
            True,
        )
    ]


@pytest.mark.parametrize(
    "stdout, message",
    [
        (_runner_inspect_payload(), "exactly one canonical staging-state host bind"),
        (
            _runner_inspect_payload(
                mounts=[
                    _runner_mount("/volume1/docker/freqtrade/state"),
                    _runner_mount("/volume1/docker/other/state"),
                ]
            ),
            "exactly one canonical staging-state host bind",
        ),
        (
            _runner_inspect_payload(
                mounts=[_runner_mount("/volume1/docker/freqtrade/state", mount_type="volume")]
            ),
            "staging-state host bind is invalid",
        ),
        (
            _runner_inspect_payload(mounts=[_runner_mount("/tmp/freqtrade/state")]),
            "staging-state host bind is invalid",
        ),
        (
            _runner_inspect_payload(
                mounts=[_runner_mount("/volume1/docker/freqtrade/../state")]
            ),
            "staging-state host bind is invalid",
        ),
        (
            _runner_inspect_payload(
                mounts=[
                    {
                        "Type": "bind",
                        "Source": "/volume1/docker/freqtrade/state",
                        "Destination": "/wrong/destination",
                    }
                ]
            ),
            "staging-state host bind is invalid",
        ),
    ],
)
def test_market_evidence_host_root_rejects_ambiguous_or_noncanonical_mounts(
    stdout: str,
    message: str,
) -> None:
    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    deploy = SimpleNamespace(_run=run, DeploymentError=RuntimeError)
    with pytest.raises(RuntimeError, match=message):
        entrypoint._resolve_market_evidence_host_root(deploy)


@pytest.mark.parametrize(
    "stdout",
    [
        "",
        "not-json\n",
        _runner_inspect_payload(
            running=False,
            mounts=[_runner_mount("/volume1/docker/freqtrade/state")],
        ),
        _runner_inspect_payload(
            project="foreign-project",
            mounts=[_runner_mount("/volume1/docker/freqtrade/state")],
        ),
        _runner_inspect_payload(
            service="foreign-service",
            mounts=[_runner_mount("/volume1/docker/freqtrade/state")],
        ),
    ],
)
def test_market_evidence_host_root_rejects_noncanonical_runner_identity(stdout: str) -> None:
    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    deploy = SimpleNamespace(_run=run, DeploymentError=RuntimeError)
    with pytest.raises(RuntimeError, match="staging runner identity is invalid"):
        entrypoint._resolve_market_evidence_host_root(deploy)
'''
    TESTS_PATH.write_text(tests[:start] + replacement, encoding="utf-8")


def patch_control_character_tests() -> None:
    control = CONTROL_PATH.read_text(encoding="utf-8")
    if "import json\n" not in control:
        control = control.replace("import importlib.util\n", "import importlib.util\nimport json\n", 1)
    start = control.index("@pytest.mark.parametrize")
    replacement = r'''@pytest.mark.parametrize(
    "source",
    [
        "/volume1/docker/freqtrade/state ",
        " /volume1/docker/freqtrade/state",
        "/volume1/docker/freqtrade/state\r",
        "/volume1/docker/freqtrade/state\n",
    ],
)
def test_market_evidence_host_root_rejects_mount_control_characters(source: str) -> None:
    mount = {
        "Type": "bind",
        "Source": source,
        "Destination": entrypoint.RUNNER_STATE_DESTINATION,
    }
    stdout = "\n".join(
        [
            "true",
            json.dumps("freqtrade-deploy-runner"),
            json.dumps("runner"),
            json.dumps(mount, separators=(",", ":")),
        ]
    ) + "\n"

    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    deploy = SimpleNamespace(_run=run, DeploymentError=RuntimeError)
    with pytest.raises(RuntimeError, match="staging-state host bind is invalid"):
        entrypoint._resolve_market_evidence_host_root(deploy)
'''
    CONTROL_PATH.write_text(control[:start] + replacement, encoding="utf-8")


def main() -> None:
    patch_entrypoint()
    patch_entrypoint_tests()
    patch_control_character_tests()


if __name__ == "__main__":
    main()
