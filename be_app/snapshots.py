"""Immutable calculation boundary. No widget/session/network access."""

import hashlib
import json
from dataclasses import dataclass

import pandas as pd

from be_app import __version__
from be_app.domain import BeConfig, BeResult, NcaConfig, Study, canonical, digest
from be_app.nca import analyze_dataset, effective_nca_config, validate_terminal_overrides
from be_app.regulations import RULES
from be_app.replicate import analyze_regulatory_be


@dataclass(frozen=True)
class InputSnapshot:
    project_id: str
    input_revision: int
    dataset_revision: int
    config_revision: int
    input_fingerprint: str
    dataset: bytes
    study: Study
    nca_config: NcaConfig
    be_config: BeConfig

    @property
    def dataset_hash(self):
        return hashlib.sha256(self.dataset).hexdigest()

    def frame(self):
        return pd.DataFrame(json.loads(self.dataset))


def run_nca(snapshot: InputSnapshot, cache: dict[str, bytes] | None = None):
    """Reuse only exact profile/config/version keys, in a caller-owned project cache."""
    data = snapshot.frame()
    validate_terminal_overrides(snapshot.nca_config, data)
    rows, computed, reused = [], 0, 0
    for _, group in data.groupby(
        ["study_id", "subject_id", "sequence", "period", "treatment", "analyte"], sort=True
    ):
        effective, override = effective_nca_config(snapshot.nca_config, group)
        key = digest(
            dict(
                project_id=snapshot.project_id,
                records=group.astype(object).where(pd.notna(group), None).to_dict("records"),
                config=effective.model_dump(mode="json"),
                terminal_review=override.model_dump(mode="json") if override else None,
                dose=snapshot.study.dose,
                dose_unit=snapshot.study.dose_unit,
                engine_version=__version__,
                rule_set_id=snapshot.study.rule_set_id,
                rule_version=RULES[snapshot.study.rule_set_id].version
                if snapshot.study.rule_set_id in RULES
                else "unsupported",
            )
        )
        if cache is not None and key in cache:
            result = json.loads(cache[key])
            reused += 1
        else:
            result = analyze_dataset(
                group, effective, dose=snapshot.study.dose, dose_unit=snapshot.study.dose_unit
            )[0]
            if override is not None:
                result["terminal_review"] = override.model_dump(mode="json")
            computed += 1
            if cache is not None:
                if len(cache) >= 2048:
                    cache.pop(next(iter(cache)))
                cache[key] = canonical(result)
        rows.append(result)
    return rows, dict(nca_profiles_computed=computed, nca_profiles_reused=reused)


def run_abe(snapshot: InputSnapshot, nca: list[dict], endpoint: str) -> BeResult:
    return analyze_regulatory_be(pd.DataFrame(nca), endpoint, snapshot.study, snapshot.be_config)


def run_ema_abel(snapshot: InputSnapshot, endpoint: str) -> BeResult:
    if snapshot.study.rule_set_id != "EMA_HVDP_ABEL":
        return BeResult(endpoint=endpoint, method="EMA ABEL", reason="Snapshot chưa chọn EMA_HVDP_ABEL.")
    nca, _ = run_nca(snapshot)
    return run_abe(snapshot, nca, endpoint)


def run_fda_rsabe(snapshot: InputSnapshot, endpoint: str) -> BeResult:
    if snapshot.study.rule_set_id != "FDA_HVD_RSABE_2026":
        return BeResult(
            endpoint=endpoint, method="FDA RSABE", reason="Snapshot chưa chọn FDA_HVD_RSABE_2026."
        )
    nca, _ = run_nca(snapshot)
    return run_abe(snapshot, nca, endpoint)
