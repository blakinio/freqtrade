from __future__ import annotations

import pytest

from ai_platform.portal.execution.host_isolation import (
    LinuxNftablesBtrfsIsolationAttestor,
    MarketDataEgressPolicy,
)


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
            policy_version="public-data-v2",
            allowed_ipv4_cidrs=(cidr,),
            dns_resolver_ipv4_addresses=("1.1.1.1",),
        )


@pytest.mark.parametrize(
    "resolver",
    (
        "10.0.0.53",
        "127.0.0.53",
        "169.254.169.254",
        "192.168.1.1",
        "203.0.113.53",
        "::1",
        "not-an-ip",
    ),
)
def test_market_data_policy_rejects_unapproved_dns_resolvers(resolver: str) -> None:
    # The security invariant is rejection. The exact ValueError text may come from
    # ipaddress for syntactically invalid/non-IPv4 inputs and is not API contract.
    with pytest.raises(ValueError):
        MarketDataEgressPolicy(
            policy_version="public-data-v2",
            allowed_ipv4_cidrs=("8.8.8.0/24",),
            dns_resolver_ipv4_addresses=(resolver,),
        )


def test_market_data_policy_requires_explicit_dns_resolver() -> None:
    with pytest.raises(ValueError, match="approved public DNS"):
        MarketDataEgressPolicy(
            policy_version="public-data-v2",
            allowed_ipv4_cidrs=("8.8.8.0/24",),
            dns_resolver_ipv4_addresses=(),
        )


def test_market_data_policy_accepts_public_ipv4_cidr_and_dns() -> None:
    policy = MarketDataEgressPolicy(
        policy_version="public-data-v2",
        allowed_ipv4_cidrs=("1.1.1.0/24",),
        dns_resolver_ipv4_addresses=("8.8.8.8",),
        allowed_tcp_ports=(443,),
    )

    assert policy.allowed_ipv4_cidrs == ("1.1.1.0/24",)
    assert policy.dns_resolver_ipv4_addresses == ("8.8.8.8",)


def test_nftables_host_prefix_normalization_matches_kernel_json_shape() -> None:
    backend = LinuxNftablesBtrfsIsolationAttestor

    assert backend._canonical_ipv4_target("1.1.1.1/32") == "1.1.1.1"
    assert backend._canonical_ipv4_target("8.8.8.0/24") == "8.8.8.0/24"
    assert (
        backend._normalize_nft_value({"prefix": {"addr": "1.1.1.1", "len": 32}})
        == "1.1.1.1"
    )
