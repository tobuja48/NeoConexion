from app.domain.matching.models import Candidate, Breakdown, MatchResult
from app.services.matching_service import MatchingService

def test_total_is_before_limit_and_ties_use_identifier():
    result = MatchResult(80, Breakdown(80,80,80,80), (), (), ())
    candidates = [Candidate(i,"Ana","Lima",1,(),"any") for i in ("b","a")]
    total, pairs = MatchingService._rank([(c,result) for c in candidates], 1, 80)
    assert total == 2
    assert pairs[0][0].id == "a"
    assert MatchingService._rank([(c,result) for c in candidates], 10, 81) == (0, [])
