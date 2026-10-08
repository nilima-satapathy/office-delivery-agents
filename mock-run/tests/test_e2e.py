import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.fleet import SAMPLE, list_aircraft
from frontend.page import render


def test_technician_sees_each_tail_and_status():
    status, body = list_aircraft(SAMPLE, "tech-1")
    page = render(status, body)
    assert "N123 serviceable" in page
    assert "N456 in_maintenance" in page
    assert "N789 grounded" in page


def test_empty_fleet_and_forbidden_pages():
    status, body = list_aircraft((), "tech-1")
    assert render(status, body) == "No aircraft"
    status, body = list_aircraft(SAMPLE, "stranger")
    assert render(status, body) == "Forbidden"
