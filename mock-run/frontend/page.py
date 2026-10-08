"""Render the fleet page from an API result. No browser."""


def render(status_code, body):
    if status_code == 403:
        return "Forbidden"
    aircraft = body.get("aircraft", [])
    if not aircraft:
        return "No aircraft"
    return "\n".join(f"{item['tail']} {item['status']}" for item in aircraft)
