import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.fleet import SAMPLE, list_aircraft


def test_get_aircraft_with_token():
    status, body = list_aircraft(SAMPLE, "tech-1")
    assert status == 200
    assert [item["tail"] for item in body["aircraft"]] == ["N123", "N456", "N789"]
    json.dumps(body)


def test_missing_token_is_forbidden():
    status, body = list_aircraft(SAMPLE, None)
    assert status == 403
    assert body["error"] == "forbidden"
