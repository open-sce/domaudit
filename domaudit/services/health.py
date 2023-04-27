import logging

from flask_healthz import HealthError

from domaudit import FLASK_APP_NAME


logger = logging.getLogger(FLASK_APP_NAME)


def check_liveness() -> None:
    try:
        logger.debug("app is alive")
    except Exception:
        raise HealthError("app is not alive -- could not log a message")


def check_readiness() -> None:
    try:
        logger.debug("app is ready")
    except Exception:
        raise HealthError("app is not ready -- could not log a message")