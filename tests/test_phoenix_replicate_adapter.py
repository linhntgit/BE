import math

import pandas as pd
import pytest

from scripts.benchmark_replicate_phoenix import wide_to_long


def test_declared_phoenix_log_mapping_preserves_sequence_and_missing_cells():
    source = pd.DataFrame(
        [
            dict(
                Subject="001",
                Sequence="BABA",
                LOG_DATA_R1=math.log(2),
                LOG_DATA_R2=math.log(3),
                LOG_DATA_T1=math.log(4),
                LOG_DATA_T2=float("nan"),
            ),
        ]
    )
    data = wide_to_long(source)
    assert data.subject_id.tolist() == ["001"] * 4
    assert data.treatment.tolist() == ["R", "T", "R", "T"]
    assert data.sequence.tolist() == ["RTRT"] * 4
    assert data.parameter.iloc[:3].tolist() == pytest.approx([2, 4, 3])
    assert math.isnan(data.parameter.iloc[3])


def test_phoenix_adapter_rejects_duplicate_subject_or_unknown_sequence():
    with pytest.raises(ValueError, match="duplicate"):
        wide_to_long(pd.DataFrame({"Subject": ["1", "1"], "Sequence": ["TRTR", "RTRT"]}))
    with pytest.raises(ValueError, match="Unknown"):
        wide_to_long(pd.DataFrame({"Subject": ["1"], "Sequence": ["ABBA"]}))
