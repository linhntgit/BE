"""Experimental estimators stay disconnected from decisions while being qualified."""

import ast
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from be_app.replicate_abe_experimental import ReplicateLikelihood, fit_full_replicate_abe
from tests.replicate_error_contrast_oracle import fit_error_contrasts


def synthetic_full4(n=24, n_trtr=None):
    rng = np.random.default_rng(20261031)
    rows = []
    for subject in range(n):
        sequence = "TRTR" if subject < (n // 2 if n_trtr is None else n_trtr) else "RTRT"
        random = rng.multivariate_normal([0, 0], [[0.15, 0.025], [0.025, 0.25]])
        for period, treatment in enumerate(sequence, 1):
            k = int(treatment == "T")
            y = 3 + 0.1 * k + 0.03 * period + 0.04 * (sequence == "TRTR")
            y += random[k] + rng.normal(0, [0.16, 0.28][k])
            rows.append(
                dict(
                    subject_id=f"S{subject:03d}",
                    sequence=sequence,
                    period=period,
                    treatment=treatment,
                    cmax=math.exp(y),
                )
            )
    return pd.DataFrame(rows)


def test_interior_imbalanced_against_independent_error_contrast_reml():
    data = synthetic_full4(n=30, n_trtr=9)
    # Run the independent computation first; neither program receives the other's fit.
    reference = fit_error_contrasts(data)
    result = fit_full_replicate_abe(data, "cmax")
    assert not result["boundary"] and reference["random_eigenvalues"].min() > 1e-3
    g = result["random_covariance"]
    actual = [g[0][0], g[0][1], g[1][1], result["residual_variance_r"], result["residual_variance_t"]]
    assert actual == pytest.approx(reference["covariance"], abs=2e-6, rel=2e-5)
    for key in ("estimate", "se", "ci90"):
        assert result[key] == pytest.approx(reference[key], abs=2e-6, rel=2e-5)
    assert result["df"] == pytest.approx(reference["df"], abs=0.01, rel=2e-4)
    assert not result["inference_allowed"] and not result["production_connected"]


def blocked_objective(data, parameters):
    """Independent block GLS calculation: no prototype transforms/projection/derivatives."""
    a, b, c, qr, qt = parameters
    g = np.array([[a * a, a * b], [a * b, b * b + c * c]])
    w = np.zeros((6, 6))
    rhs = np.zeros(6)
    quadratic = logdet = 0.0
    n = 0
    for _, block in data.groupby("subject_id"):
        block = block.sort_values("period")
        y = np.log(block.cmax.to_numpy())
        x = np.column_stack(
            [
                np.ones(4),
                block.sequence.eq("TRTR"),
                *[block.period.eq(p) for p in (1, 2, 3)],
                block.treatment.eq("T"),
            ]
        ).astype(float)
        z = np.column_stack([block.treatment.eq("R"), block.treatment.eq("T")]).astype(float)
        variance = z @ g @ z.T + np.diag(
            [math.exp(qr) if t == "R" else math.exp(qt) for t in block.treatment]
        )
        inv = np.linalg.inv(variance)
        w += x.T @ inv @ x
        rhs += x.T @ inv @ y
        quadratic += y @ inv @ y
        logdet += np.linalg.slogdet(variance)[1]
        n += 4
    assert n == len(data)
    return 0.5 * (logdet + np.linalg.slogdet(w)[1] + quadratic - rhs @ np.linalg.solve(w, rhs))


@pytest.mark.parametrize("factor_c", [0.2, 0.0])
def test_analytic_score_and_nonlinear_information_against_independent_block_differences(factor_c):
    data = synthetic_full4(n=8)
    model = ReplicateLikelihood(data, "cmax")
    parameters = np.array([0.3, 0.08, factor_c, math.log(0.02), math.log(0.05)])
    state = model.evaluate(parameters, information=True)
    expected = blocked_objective(data, parameters)
    assert state["objective"] == pytest.approx(expected, abs=2e-10)
    steps = np.array([1e-4] * 3 + [4e-4] * 2)
    gradient = np.zeros(5)
    information = np.zeros((5, 5))
    for i in range(5):
        di = np.eye(5)[i] * steps[i]
        positive = blocked_objective(data, parameters + di)
        negative = blocked_objective(data, parameters - di)
        gradient[i] = (positive - negative) / (2 * steps[i])
        information[i, i] = (positive - 2 * expected + negative) / steps[i] ** 2
        for j in range(i):
            dj = np.eye(5)[j] * steps[j]
            information[i, j] = information[j, i] = (
                blocked_objective(data, parameters + di + dj)
                - blocked_objective(data, parameters + di - dj)
                - blocked_objective(data, parameters - di + dj)
                + blocked_objective(data, parameters - di - dj)
            ) / (4 * steps[i] * steps[j])
    assert state["gradient"] == pytest.approx(gradient, abs=5e-4, rel=5e-5)
    assert state["hessian"] == pytest.approx(information, abs=5e-3, rel=3e-4)


def test_experimental_fit_invariants_and_closed_decision_gate():
    data = synthetic_full4()
    result = fit_full_replicate_abe(data, "cmax")
    transformed = data.sample(frac=1, random_state=42).copy()
    transformed["subject_id"] = transformed.subject_id.map(lambda value: "renamed_" + value[::-1])
    transformed["cmax"] *= 1000
    repeat = fit_full_replicate_abe(transformed, "cmax")
    for key in ("estimate", "se", "df", "gmr", "reml_log_likelihood"):
        assert repeat[key] == pytest.approx(result[key], abs=2e-5, rel=1e-6)
    assert np.linalg.eigvalsh(result["random_covariance"]).min() >= -1e-12
    assert result["residual_variance_r"] > 0 and result["residual_variance_t"] > 0
    assert not result["inference_allowed"] and not result["production_connected"]
    assert "decision" not in result and "criteria" not in result
    assert len(result["population"]) == len(data)
    assert sum(attempt["converged"] for attempt in result["optimizer_attempts"]) >= 2


def test_treatment_reversal_preserves_uncertainty_and_swaps_covariance():
    data = synthetic_full4()
    original = fit_full_replicate_abe(data, "cmax")
    data["treatment"] = data.treatment.map({"R": "T", "T": "R"})
    data["sequence"] = data.sequence.map({"RTRT": "TRTR", "TRTR": "RTRT"})
    reverse = fit_full_replicate_abe(data, "cmax")
    assert reverse["estimate"] == pytest.approx(-original["estimate"], abs=1e-7)
    for key in ("se", "df", "reml_log_likelihood"):
        assert reverse[key] == pytest.approx(original[key], abs=2e-5, rel=1e-6)
    assert reverse["ci90"] == pytest.approx([1 / x for x in original["ci90"][::-1]], abs=1e-7)
    assert reverse["random_covariance"] == pytest.approx(np.array(original["random_covariance"])[::-1, ::-1], abs=1e-7)
    assert reverse["residual_variance_r"] == pytest.approx(original["residual_variance_t"], abs=1e-7)
    assert not reverse["inference_allowed"]


def test_invalid_missing_and_nonconvergent_inputs_never_produce_experimental_inference():
    data = synthetic_full4(n=8)
    with pytest.raises(ValueError, match="required columns"):
        fit_full_replicate_abe(data.drop(columns="subject_id"), "cmax")
    with pytest.raises(ValueError):
        fit_full_replicate_abe(data.iloc[1:], "cmax")
    with pytest.raises(ValueError):
        fit_full_replicate_abe(pd.concat([data, data.iloc[:1]]), "cmax")
    with pytest.raises(ValueError, match="did not converge"):
        fit_full_replicate_abe(data, "cmax", max_iterations=0)
    for missing in (None, "", "  "):
        invalid = data.copy()
        invalid.loc[invalid.subject_id.eq("S000"), "subject_id"] = missing
        with pytest.raises(ValueError, match="missing subject identifiers"):
            fit_full_replicate_abe(invalid, "cmax")
    data["cmax"] = 10.0
    with pytest.raises(ValueError, match="Degenerate"):
        fit_full_replicate_abe(data, "cmax")


def test_production_modules_do_not_import_experimental_model():
    root = Path(__file__).resolve().parents[1] / "be_app"
    for name in ("pipeline.py", "ui.py", "replicate.py", "statistics.py"):
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert "replicate_abe_experimental" not in (node.module or "")
