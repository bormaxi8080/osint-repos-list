"""JSON generation helpers for OSINT repositories list."""

import json


def save_json(path, json_data):
    """Write JSON data to disk with indentation."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
