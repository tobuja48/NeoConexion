import pytest
from app.domain.matching.experience import experience_score

@pytest.mark.parametrize("years,required,expected", [(0,0,100),(1.5,3,50),(5,3,100),(0,3,0)])
def test_experience_ratio(years, required, expected):
    assert experience_score(years, required) == expected
