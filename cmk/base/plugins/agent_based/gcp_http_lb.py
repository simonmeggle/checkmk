#!/usr/bin/env python3
# Copyright (C) 2022 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
# mypy: disallow_untyped_defs
from typing import Any, Mapping, Optional

from .agent_based_api.v1 import register, render, Service, ServiceLabel
from .agent_based_api.v1.type_defs import CheckResult, DiscoveryResult, StringTable
from .utils import gcp


def parse(string_table: StringTable) -> gcp.Section:
    return gcp.parse_gcp(string_table, gcp.ResourceKey("url_map_name"))


register.agent_section(name="gcp_service_http_lb", parse_function=parse)


service_namer = gcp.service_name_factory("HTTP(S) load balancer")
SECTIONS = ["gcp_service_http_lb", "gcp_assets"]
ASSET_TYPE = gcp.AssetType("compute.googleapis.com/UrlMap")


def discover(
    section_gcp_service_http_lb: Optional[gcp.Section],
    section_gcp_assets: Optional[gcp.AssetSection],
) -> DiscoveryResult:
    if (
        section_gcp_assets is None
        or not section_gcp_assets.config.is_enabled("http_lb")
        or not ASSET_TYPE in section_gcp_assets
    ):
        return
    for item, _ in section_gcp_assets[ASSET_TYPE].items():
        labels = [ServiceLabel("gcp/projectId", section_gcp_assets.project)]
        yield Service(item=item, labels=labels)


def check_requests(
    item: str,
    params: Mapping[str, Any],
    section_gcp_service_http_lb: Optional[gcp.Section],
    section_gcp_assets: Optional[gcp.AssetSection],
) -> CheckResult:
    metrics = {
        "requests": gcp.MetricSpec(
            "loadbalancing.googleapis.com/https/request_count", "Requests", str
        )
    }
    yield from gcp.check(
        metrics, item, params, section_gcp_service_http_lb, ASSET_TYPE, section_gcp_assets
    )


register.check_plugin(
    name="gcp_http_lb_requests",
    sections=SECTIONS,
    service_name=service_namer("requests"),
    check_ruleset_name="gcp_http_lb_requests",
    discovery_function=discover,
    check_function=check_requests,
    check_default_parameters={"requests": None},
)


def check_latencies(
    item: str,
    params: Mapping[str, Any],
    section_gcp_service_http_lb: Optional[gcp.Section],
    section_gcp_assets: Optional[gcp.AssetSection],
) -> CheckResult:
    metrics = {
        "latencies": gcp.MetricSpec(
            "loadbalancing.googleapis.com/https/total_latencies",
            "Latency",
            render.timespan,
            scale=1e-3,
        )
    }
    yield from gcp.check(
        metrics, item, params, section_gcp_service_http_lb, ASSET_TYPE, section_gcp_assets
    )


register.check_plugin(
    name="gcp_http_lb_latencies",
    sections=SECTIONS,
    service_name=service_namer("latencies"),
    check_ruleset_name="gcp_http_lb_latencies",
    discovery_function=discover,
    check_function=check_latencies,
    check_default_parameters={"latencies": None},
)


def discovery_summary(section: gcp.AssetSection) -> DiscoveryResult:
    yield from gcp.discovery_summary(section, "HTTP_LB")


def check_summary(section: gcp.AssetSection) -> CheckResult:
    yield from gcp.check_summary(ASSET_TYPE, "load balancer", section)


register.check_plugin(
    name="gcp_http_lb_summary",
    sections=["gcp_assets"],
    service_name=service_namer.summary_name(),
    discovery_function=discovery_summary,
    check_function=check_summary,
)
