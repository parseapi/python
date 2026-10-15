"""Safe identity choices on an explicit City ambiguity error."""
import re
from typing import Any, List, Literal, Optional, TypedDict, cast

class _CityCandidateIdentity(TypedDict):
    id: str
    object: Literal['city']

class CityAmbiguityCandidate(_CityCandidateIdentity, total=False):
    name: Optional[str]
    name_local: Optional[str]
    country: Optional[str]
    country_name: Optional[str]
    state: Optional[str]
    state_name: Optional[str]
    type: Optional[str]


def city_error_candidates(value: Any) -> Optional[List[CityAmbiguityCandidate]]:
    if not isinstance(value, list):
        return None
    candidates = []
    for row in value[:2]:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not re.fullmatch(r'city_[23456789abcdefghjkmnpqrstuvwxyz]{12}', row['id']) or row.get('object') != 'city':
            continue
        candidate = {'id': row['id'], 'object': 'city'}
        for key in ('name', 'name_local', 'country', 'country_name', 'state', 'state_name', 'type'):
            if key in row and (row[key] is None or isinstance(row[key], str) and len(row[key]) <= 255):
                candidate[key] = row[key]
        candidates.append(cast(CityAmbiguityCandidate, candidate))
    return candidates
