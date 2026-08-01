#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


DEPLOYMENT_DIR = Path(__file__).resolve().parent


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load deployment module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    deploy = _load_module("portal_oidc_deploy", DEPLOYMENT_DIR / "deploy.py")
    discovery = _load_module(
        "portal_oidc_discovery",
        DEPLOYMENT_DIR / "diagnose_discovery.py",
    )
    deploy._discovery_from_identity_container = lambda: discovery.deployment_probe(
        deploy.DeploymentError
    )
    return int(deploy.main())


if __name__ == "__main__":
    sys.exit(main())
