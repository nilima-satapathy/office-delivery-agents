import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.fleet import list_aircraft


def test_known_token_returns_tails_and_status():
    status, body = list_aircraft(
        [{"tail": "N123", "status": "serviceable"}],
        "tech-1",
    )
    assert status == 200
    assert body["aircraft"] == [{"tail": "N123", "status": "serviceable"}]


def test_unknown_status_is_rejected():
    try:
        list_aircraft([{"tail": "N1", "status": "lost"}], "tech-1")
    except ValueError as error:
        assert "unknown status" in str(error)
    else:
        raise AssertionError("unknown status was accepted")
