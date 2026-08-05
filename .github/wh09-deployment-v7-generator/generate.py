from __future__ import annotations

from pathlib import Path
import sys


OLD_WORKFLOW = ".github/workflows/wickhunter-wh09-deploy-20260805-v6.yml"
NEW_WORKFLOW = ".github/workflows/wickhunter-wh09-deploy-20260805-v7.yml"

OLD_NETWORK_BLOCK = '''          docker network create --internal "$INTERNAL_NETWORK" >/dev/null
          network_created=true
          subnet="$(docker network inspect --format '{{ (index .IPAM.Config 0).Subnet }}' "$INTERNAL_NETWORK")"
          read -r gateway_ip operator_ip probe_ip < <(
            python3 - "$subnet" <<'PY'
          import ipaddress
          import sys
          network = ipaddress.ip_network(sys.argv[1], strict=True)
          hosts = list(network.hosts())
          if len(hosts) < 5:
              raise SystemExit("internal Docker subnet is too small")
          print(hosts[1], hosts[2], hosts[3])
          PY
          )
'''

NEW_NETWORK_BLOCK = '''          existing_subnets=""
          while IFS= read -r network_id; do
            [[ -n "$network_id" ]] || continue
            network_subnets="$(docker network inspect --format '{{range .IPAM.Config}}{{println .Subnet}}{{end}}' "$network_id")"
            existing_subnets+="$network_subnets"$'\\n'
          done < <(docker network ls -q)
          read -r subnet gateway_ip operator_ip probe_ip < <(
            EXISTING_SUBNETS="$existing_subnets" python3 - <<'PY'
          import ipaddress
          import os

          occupied: list[ipaddress.IPv4Network] = []
          for raw in os.environ.get("EXISTING_SUBNETS", "").splitlines():
              value = raw.strip()
              if not value:
                  continue
              try:
                  network = ipaddress.ip_network(value, strict=False)
              except ValueError:
                  continue
              if isinstance(network, ipaddress.IPv4Network):
                  occupied.append(network)

          pool = ipaddress.ip_network("172.31.240.0/20")
          for candidate in pool.subnets(new_prefix=29):
              if any(candidate.overlaps(existing) for existing in occupied):
                  continue
              hosts = list(candidate.hosts())
              print(candidate.with_prefixlen, hosts[1], hosts[2], hosts[3])
              break
          else:
              raise SystemExit("no non-overlapping WH09 internal subnet is available")
          PY
          )
          [[ -n "$subnet" && -n "$gateway_ip" && -n "$operator_ip" && -n "$probe_ip" ]]
          docker network create --internal --subnet "$subnet" "$INTERNAL_NETWORK" >/dev/null
          network_created=true
          actual_subnet="$(docker network inspect --format '{{ (index .IPAM.Config 0).Subnet }}' "$INTERNAL_NETWORK")"
          [[ "$actual_subnet" == "$subnet" ]]
'''


def replace_exact(text: str, old: str, new: str, *, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"expected {expected} occurrences of marker, found {count}: {old[:120]!r}")
    return text.replace(old, new)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: generate.py SOURCE OUTPUT")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    text = source.read_text(encoding="utf-8")
    text = replace_exact(text, OLD_NETWORK_BLOCK, NEW_NETWORK_BLOCK)
    text = replace_exact(text, OLD_WORKFLOW, NEW_WORKFLOW, expected=3)
    text = replace_exact(
        text,
        'raise SystemExit("gateway requires an IPv6 internal address")',
        'raise SystemExit("gateway requires an IPv4 internal address")',
    )
    if "v6" not in text:
        raise SystemExit("source workflow has no v6 identities")
    text = text.replace("v6", "v7")

    required = (
        "name: WickHunter WH09 fresh PAPER deployment v7",
        "group: wickhunter-wh09-deploy-v7",
        NEW_WORKFLOW,
        "ACTIVATION_NAME: wickhunter-wh09-activation-20260805-v7-4fde185a",
        "BOT_INSTANCE: wickhunter-paper-v7",
        "OPERATOR_CONTAINER: wickhunter-paper-runtime-v7",
        "GATEWAY_CONTAINER: wickhunter-wh09-egress-v7",
        "INTERNAL_NETWORK: wickhunter-wh09-internal-v7",
        'state_runner="$RUNNER_STATE_ROOT/wickhunter-paper-runtime/v7"',
        'docker network create --internal --subnet "$subnet" "$INTERNAL_NETWORK"',
        'pool = ipaddress.ip_network("172.31.240.0/20")',
        'EXISTING_SUBNETS="$existing_subnets" python3',
        'raise SystemExit("gateway requires an IPv4 internal address")',
        'operator = by_name["wickhunter-paper-runtime-v7"]',
        'gateway = by_name["wickhunter-wh09-egress-v7"]',
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"generated workflow missing markers: {missing!r}")

    forbidden = (OLD_WORKFLOW, "v6", "docker network create --internal \"$INTERNAL_NETWORK\"")
    present = [item for item in forbidden if item in text]
    if present:
        raise SystemExit(f"generated workflow retains stale or unsafe markers: {present!r}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
