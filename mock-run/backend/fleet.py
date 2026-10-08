"""In-memory fleet status for the local mock story MOCK-2."""

STATUSES = ("serviceable", "in_maintenance", "grounded")
KNOWN_TOKENS = {"tech-1"}
SAMPLE = (
    {"tail": "N123", "status": "serviceable"},
    {"tail": "N456", "status": "in_maintenance"},
    {"tail": "N789", "status": "grounded"},
)


def list_aircraft(records, token):
    if token not in KNOWN_TOKENS:
        return 403, {"error": "forbidden"}
    body = []
    for record in records:
        if record["status"] not in STATUSES:
            raise ValueError(f"unknown status: {record['status']}")
        body.append({"tail": record["tail"], "status": record["status"]})
    return 200, {"aircraft": body}
