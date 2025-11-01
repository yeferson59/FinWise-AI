"""Tests for health service."""

from app.services import health


def test_get_health_status_app():
    """Test that health status returns OK."""
    result = health.get_health_status_app()
    
    assert result is not None
    assert isinstance(result, dict)
    assert "status" in result
    assert result["status"] == "OK"
