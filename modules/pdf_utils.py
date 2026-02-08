"""General PDF utilities."""

from datetime import datetime


def _format_github_date(value):
    """Format GitHub ISO dates to YYYY-MM-DD."""
    if not value:
        return "unknown"
    try:
        return datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")
    except ValueError:
        return str(value)
