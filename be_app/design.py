"""Reproducible balanced block allocation and exact numerical TOST power."""

import math
import random
import secrets
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.special import ndtr
from scipy.stats import chi2, t

from be_app.domain import digest

SEQUENCES = {
    "2x2": ("TR", "RT"),
    "parallel": ("T", "R"),
    "partial3": ("TRR", "RTR", "RRT"),
    "full4": ("TRTR", "RTRT"),
}


def secure_seed() -> int:
    return secrets.randbits(63)


def randomize(design: str, n: int, seed: int, block_size: int | None = None):
    if design not in SEQUENCES:
        raise ValueError("Thiết kế chưa hỗ trợ.")
    sequences = SEQUENCES[design]
    block = block_size or len(sequences) * 2
    if n < len(sequences) or block < len(sequences) or block % len(sequences) or n % len(sequences):
        raise ValueError("n và block phải là bội số của số sequence; mỗi sequence cần ít nhất một người.")
    rng = random.Random(seed)
    allocations = []
    for start in range(0, n, block):
        chunk = list(sequences) * (min(block, n - start) // len(sequences))
        rng.shuffle(chunk)
        allocations.extend(chunk)
    rows = []
    for i, seq in enumerate(allocations, start=1):
        for period, treatment in enumerate(seq, start=1):
            rows.append(
                dict(
                    subject_id=f"S{i:04d}",
                    randomization_id=f"{i:05d}",
                    screening_id=f"SCR{i:05d}",
                    sequence=seq,
                    period=period,
                    treatment=treatment,
                    cohort="1",
                    status="Planned",
                )
            )
    metadata = dict(
        design=design,
        n=n,
        seed=seed,
        block_size=block,
        generator="python.random.MT19937 / balanced blocks v1",
    )
    metadata["hash"] = digest({"rows": rows, "metadata": metadata})
    return pd.DataFrame(rows), metadata


def sample_schedule(allocation: pd.DataFrame, times: list[float]) -> pd.DataFrame:
    if not times or any(not math.isfinite(x) or x < 0 for x in times) or len(times) != len(set(times)):
        raise ValueError("Thời điểm dự kiến phải hữu hạn, không âm, không trùng.")
    return allocation.merge(pd.DataFrame({"nominal_time_h": sorted(times)}), how="cross").assign(
        dose_datetime="", sample_datetime="", actual_time_h=""
    )


def tost_power(
    cv: float,
    gmr: float,
    n1: int,
    n2: int,
    design: str = "2x2",
    alpha: float = 0.05,
    lower: float = 0.8,
    upper: float = 1.25,
) -> float:
    """Exact joint rejection probability, not the difference of marginal t powers.

    Integrate the conditional normal interval over independent residual chi-square.
    Equal log variances and complete observations; parallel counts are arm counts,
    crossover counts are sequence counts. CV is a fraction (0.20 = 20%).
    """
    if design not in ("2x2", "parallel"):
        raise ValueError("Power replicate chưa hỗ trợ khi chưa có benchmark.")
    if not all(math.isfinite(x) for x in (cv, gmr, alpha, lower, upper)):
        raise ValueError("Tham số phải hữu hạn.")
    if not 0 < cv <= 5 or gmr <= 0 or not 0 < alpha < 0.5 or not 0 < lower < upper:
        raise ValueError("CV dạng tỷ lệ trong (0,5], GMR > 0, alpha và giới hạn phải hợp lệ.")
    if any(isinstance(x, bool) or int(x) != x or x < 2 for x in (n1, n2)):
        raise ValueError("Mỗi nhánh/sequence cần ít nhất 2 người, dạng số nguyên.")
    df = n1 + n2 - 2
    sigma = math.sqrt(math.log1p(cv * cv))
    factor = 0.5 if design == "2x2" else 1.0
    se = sigma * math.sqrt(factor * (1 / n1 + 1 / n2))
    critical = t.ppf(1 - alpha, df)
    lo, hi, delta = math.log(lower), math.log(upper), math.log(gmr)
    vmax = min(df * ((hi - lo) / (2 * critical * se)) ** 2, chi2.ppf(1 - 1e-13, df))

    def integrand(v):
        margin = critical * math.sqrt(v / df)
        probability = max(0.0, ndtr((hi - delta) / se - margin) - ndtr((lo - delta) / se + margin))
        return probability * chi2.pdf(v, df)

    points = [p for p in chi2.ppf([0.001, 0.1, 0.5, 0.9, 0.999], df) if 0 < p < vmax]
    value, error = quad(integrand, 0, vmax, points=points, epsabs=1e-10, epsrel=1e-9, limit=200)
    if error > 1e-7:
        raise ArithmeticError("Tích phân power chưa hội tụ tới dung sai yêu cầu.")
    return float(np.clip(value, 0, 1))


@dataclass(frozen=True)
class SampleSize:
    evaluable: int
    recruit: int
    per_group: int
    achieved_power: float
    dropout: float
    cv_type: str


def sample_size(
    cv: float,
    gmr: float = 0.95,
    target: float = 0.8,
    design: str = "2x2",
    dropout: float = 0.1,
    minimum_per_group: int | None = None,
    max_n: int = 10000,
    *,
    alpha: float = 0.05,
    lower: float = 0.8,
    upper: float = 1.25,
) -> SampleSize:
    if not all(math.isfinite(x) for x in (cv, gmr, target, dropout, alpha, lower, upper)):
        raise ValueError("Các tham số cỡ mẫu phải hữu hạn.")
    if not 0 < target < 1 or not 0 <= dropout < 1 or not 0 < lower < upper or not lower < gmr < upper:
        raise ValueError("Power/dropout phải hợp lệ; GMR phải nằm trong giới hạn của endpoint đang tính.")
    if not 0 < alpha < 0.5:
        raise ValueError("Alpha phải nằm trong (0, 0.5).")
    if design not in ("2x2", "parallel"):
        raise ValueError("Cỡ mẫu replicate chưa hỗ trợ.")
    minimum = minimum_per_group if minimum_per_group is not None else (6 if design == "2x2" else 12)
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 2 or max_n < minimum * 2:
        raise ValueError("Số người tối thiểu và giới hạn tìm kiếm phải hợp lệ.")
    for per_group in range(minimum, max_n // 2 + 1):
        power = tost_power(cv, gmr, per_group, per_group, design, alpha, lower, upper)
        if power >= target:
            return SampleSize(
                2 * per_group,
                2 * math.ceil(per_group / (1 - dropout)),
                per_group,
                power,
                dropout,
                "CVw" if design == "2x2" else "CV total giữa người",
            )
    raise ValueError("Không tìm được cỡ mẫu trong giới hạn tìm kiếm.")
