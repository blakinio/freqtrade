from __future__ import annotations

import pytest

from ai_platform.portal.execution.host_isolation import MarketDataEgressPolicy


@pytest.mark.parametrize(
    "cidr",
    (
        "0.0.0.0/0",
        "8.0.0.0/5",
        "10.0.0.0/8",
        "100.64.0.0/10",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "198.18.0.0/15",
        "203.0.113.0/24",
        "224.0.0.0/4",
        "240.0.0.0/4",
    ),
)
def test_market_data_policy_rejects_non_public_or_overlapping_cidrs(cidr: str) -> None:
    with pytest.raises(ValueError, match="exclusively public"):
        MarketDataEgressPolicy(
            policy_version="public-data-v1",
            allowed_ipv4_cidrs=(cidr,),
        )


def test_market_data_policy_accepts_public_ipv4_cidr() -> None:
    policy = MarketDataEgressPolicy(
        policy_version="public-data-v1",
        allowed_ipv4_cidrs=("1.1.1.0/24",),
        allowed_tcp_ports=(443,),
    )

    assert policy.allowed_ipv4_cidrs == ("1.1.1.0/24",)
