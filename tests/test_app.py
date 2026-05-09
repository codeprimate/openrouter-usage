"""Smoke tests for the Textual app."""

from openrouter_usage.app import UsageApp


def test_usage_app_construct() -> None:
    app = UsageApp(management_key="test-key")
    assert app.management_key == "test-key"


def test_usage_app_format_title_puts_version_after_name() -> None:
    app = UsageApp(management_key="test-key")
    rendered = str(app.format_title("openrouter-usage", "0.1.0"))
    assert rendered.startswith("openrouter-usage")
    assert rendered.endswith("0.1.0")


def test_usage_app_leaves_textual_line_filters_intact() -> None:
    """Textual App uses self._filters for LineFilter instances; do not store ClientFilters there."""
    app = UsageApp(management_key="test-key")
    for f in app._filters:
        assert hasattr(f, "enabled")
