import pytest


def test_log_interactive_non_geoips(caplog):
    """Ensure that log.interactive fails for standard logging module.

    This is to ensure that GeoIPS"""
    import logging

    log = logging.getLogger(__name__)
    with pytest.raises(AttributeError):
        log.interactive("FROM PYTEST")


def test_log_interactive_geoips(caplog):
    from geoips.__init__ import logging as gi_logging

    log = gi_logging.getLogger(__name__)

    log.interactive("FROM PYTEST")
    assert "FROM PYTEST" in caplog.text
    assert "INTERACTIVE" in caplog.text
