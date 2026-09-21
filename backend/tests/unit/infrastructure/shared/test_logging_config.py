import logging

import pytest

from src.shared.infrastructure.logging_config import configure_logging


@pytest.mark.parametrize("name", ["httpcore.http11", "httpcore.proxy", "httpx", "zeep.transports"])
def test_third_party_http_loggers_stay_quiet_with_debug_root(name: str) -> None:
    configure_logging(level="DEBUG")

    logger = logging.getLogger(name)

    assert logging.getLogger().level == logging.DEBUG
    assert not logger.isEnabledFor(logging.DEBUG)
    assert logger.isEnabledFor(logging.WARNING)
