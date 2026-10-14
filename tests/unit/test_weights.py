import pytest
from app.domain.matching.weights import Weights

@pytest.mark.parametrize("value", [-1, 2, float("nan"), float("inf"), 0.51])
def test_weights_reject_invalid_sum_or_range(value):
    with pytest.raises(ValueError):
        Weights(skills=value)

def test_custom_valid_weights():
    assert Weights(1, 0, 0, 0).skills == 1
