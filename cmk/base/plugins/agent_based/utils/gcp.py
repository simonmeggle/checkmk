#!/usr/bin/env python3
# Copyright (C) 2022 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
# mypy: disallow_untyped_defs
import json
from dataclasses import dataclass
from enum import IntEnum, unique
from typing import Any, Callable, Mapping, NewType, Optional, Sequence, Union

from ..agent_based_api.v1 import check_levels, check_levels_predictive, Result, Service, State
from ..agent_based_api.v1.type_defs import CheckResult, DiscoveryResult, StringTable

Project = str


@dataclass(frozen=True)
class ResourceKey:
    key: str
    prefix: str = "resource"


@dataclass(frozen=True)
class MetricKey:
    key: str
    prefix: str = "metric"


Key = Union[ResourceKey, MetricKey]


@dataclass(frozen=True)
class GCPLabels:
    _data: Mapping[str, Any]

    def __getitem__(self, key: Key) -> str:
        return self._data[key.prefix]["labels"][key.key]


@dataclass(frozen=True)
class GCPResult:
    _ts: Mapping[str, Any]
    labels: GCPLabels

    @classmethod
    def deserialize(cls, data: str) -> "GCPResult":
        parsed = json.loads(data)
        return cls(_ts=parsed, labels=GCPLabels(parsed))

    @property
    def metric_type(self) -> str:
        return self._ts["metric"]["type"]

    @property
    def value_type(self) -> int:
        return self._ts["value_type"]

    @property
    def points(self) -> Sequence[Mapping[str, Any]]:
        return self._ts["points"]


AssetType = NewType("AssetType", str)


@dataclass(frozen=True)
class GCPAsset:
    _asset: Mapping[str, Any]

    @classmethod
    def deserialize(cls, data: str) -> "GCPAsset":
        return cls(_asset=json.loads(data))

    @property
    def resource_data(self) -> Mapping[str, Any]:
        return self._asset["resource"]["data"]

    @property
    def location(self) -> str:
        return self._asset["resource"]["location"]

    @property
    def asset_type(self) -> AssetType:
        return self._asset["asset_type"]


@dataclass(frozen=True)
class SectionItem:
    rows: Sequence[GCPResult]


@dataclass(frozen=True)
class Config:
    services: Sequence[str]

    def is_enabled(self, service: str) -> bool:
        return service in self.services


PiggyBackSection = Sequence[GCPResult]
Item = str
AssetTypeSection = Mapping[Item, GCPAsset]
Section = Mapping[Item, SectionItem]


@dataclass(frozen=True)
class AssetSection:
    project: Project
    config: Config
    _assets: Mapping[AssetType, AssetTypeSection]

    def __getitem__(self, key: AssetType) -> AssetTypeSection:
        return self._assets[key]

    def get(
        self, key: AssetType, default: Optional[AssetTypeSection] = None
    ) -> Optional[AssetTypeSection]:
        return self._assets.get(key, default)

    def __contains__(self, key: AssetType) -> bool:
        return key in self._assets


def parse_gcp(
    string_table: StringTable, label_key: Key, extract: Callable[[str], str] = lambda x: x
) -> Section:
    rows = [GCPResult.deserialize(row[0]) for row in string_table]
    items = {row.labels[label_key] for row in rows}
    return {
        extract(item): SectionItem([r for r in rows if r.labels[label_key] == item])
        for item in items
    }


def parse_piggyback(string_table: StringTable) -> PiggyBackSection:
    return [GCPResult.deserialize(row[0]) for row in string_table]


@dataclass(frozen=True)
class Filter:
    key: Key
    value: str


@dataclass(frozen=True)
class MetricSpec:
    @unique
    class DType(IntEnum):
        INT = 2
        FLOAT = 3

    metric_type: str
    label: str
    render_func: Callable
    scale: float = 1.0
    filter_by: Optional[Filter] = None


def get_value(results: Sequence[GCPResult], spec: MetricSpec) -> float:
    # GCP does not always deliver all metrics. i.e. api/request_count only contains values if
    # api requests have occured. To ensure all metrics are displayed in check mk we default to
    # 0 in the absence of data.

    if spec.filter_by is not None:
        filter_by = spec.filter_by

        def filter_func(r: GCPResult) -> bool:
            return r.metric_type == spec.metric_type and r.labels[filter_by.key] == filter_by.value

    else:

        def filter_func(r: GCPResult) -> bool:
            return r.metric_type == spec.metric_type

    results = list(r for r in results if filter_func(r))
    ret_val = 0.0
    for result in results:
        proto_value = result.points[0]["value"]
        match result.value_type:
            case MetricSpec.DType.FLOAT:
                value = float(proto_value["double_value"])
            case MetricSpec.DType.INT:
                value = float(proto_value["int64_value"])
            case _:
                raise NotImplementedError("unknown dtype")
        ret_val += value * spec.scale
    return ret_val


def generic_check(
    metrics: Mapping[str, MetricSpec], timeseries: Sequence[GCPResult], params: Mapping[str, Any]
) -> CheckResult:
    for metric_name, metric_spec in metrics.items():
        value = get_value(timeseries, metric_spec)
        levels_upper = params[metric_name]
        if isinstance(levels_upper, dict):
            yield from check_levels_predictive(
                value,
                metric_name=metric_name,
                render_func=metric_spec.render_func,
                levels=levels_upper,
                label=metric_spec.label,
            )
        else:
            yield from check_levels(
                value,
                metric_name=metric_name,
                render_func=metric_spec.render_func,
                levels_upper=levels_upper,
                label=metric_spec.label,
            )


def check(
    spec: Mapping[str, MetricSpec],
    item: str,
    params: Mapping[str, Any],
    section: Optional[Section],
    asset_type: AssetType,
    all_assets: Optional[AssetSection],
) -> CheckResult:
    if section is None or not item_in_section(item, asset_type, all_assets):
        return
    timeseries = section.get(item, SectionItem(rows=[])).rows
    yield from generic_check(spec, timeseries, params)


def item_in_section(
    item: str,
    asset_type: AssetType,
    all_assets: Optional[AssetSection],
) -> bool:
    """We have to check the assets for the item. In the normal section a missing item could also indicate no data.
    This happens for example with a function that is not called."""
    return (
        all_assets is not None
        and (assets := all_assets.get(asset_type)) is not None
        and item in assets
    )


class ServiceNamer:
    def __init__(self, service: str) -> None:
        self.service = service

    def __call__(self, name: str) -> str:
        return f"{self.service} - %s - {name}"

    def summary_name(self) -> str:
        return f"{self.service} - summary"


def service_name_factory(gcp_service: str) -> ServiceNamer:
    return ServiceNamer(gcp_service)


def discovery_summary(section: AssetSection, service: str) -> DiscoveryResult:
    if section.config.is_enabled(service):
        yield Service()


def check_summary(asset_type: AssetType, descriptor: str, section: AssetSection) -> CheckResult:
    n = len(section[asset_type]) if asset_type in section else 0
    appendix = "s" if n != 1 else ""
    yield Result(
        state=State.OK,
        summary=f"{n} {descriptor}{appendix}",
        details=f"Found {n} {descriptor.lower() if not descriptor.isupper() else descriptor}{appendix}",
    )
