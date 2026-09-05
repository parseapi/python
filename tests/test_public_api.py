import importlib.util
import json
from pathlib import Path


def test_public_api_matches_reviewed_baseline():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('public_api', root / 'scripts/public_api.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.snapshot() == json.loads((root / 'api/public.json').read_text())
