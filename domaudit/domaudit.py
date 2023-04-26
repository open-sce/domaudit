import json
import sys
import os
import logging

from flask import Flask, request, Response
from flask_healthz import Healthz
import requests
from field_audit.services import constants
from field_audit import FLASK_APP_NAME

constants.DOMINO_API_HOST = os.getenv("DOMINO_API_HOST", default="http://nucleus-frontend.domino-platform:80")

def create_app(test_config=None):
    app = Flask(FLASK_APP_NAME)
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    app.config.update(
        {
            "TRAP_HTTP_EXCEPTIONS": False,
            "HEALTHZ": {
                "live": "domino_mlflow.services.health.check_liveness",
                "ready": "domino_mlflow.services.health.check_readiness",
            },
        }
    )

    Healthz(app, no_log=True)

    logging.info("Starting up Field Audit API service")
    logging.info("Domino Nucleus URI=" + constants.DOMINO_API_HOST)
    logging.info(f"Domino Public URI={constants.DOMINO_PUBLIC_URI}")

    @app.route("/project_audit", methods=["GET"])
    def project_audit(path, **kwargs):
        logging.debug(f"######## [{request.method}] {path}")
        response = None

        # TODO: get project audit, format as json, return
        # Validate user has access to project
        
        return response

    @app.route("/user_audit", methods=["GET"])
    def user_audit(path, **kwargs):
        logging.debug(f"######## [{request.method}] {path}")
        response = None

        # TODO: get User audit from keycloak, format as json, return
        # Optional time frame input. Default 30(?) days
        # Admin only
        
        return response

    @app.route("/telemetry_audit", methods=["GET"])
    def telemetry_audit(path, **kwargs):
        logging.debug(f"######## [{request.method}] {path}")
        response = None

        # TODO: get User audit from telemetry records, format as json, return
        # Required input: either user, or project, or both
        # Admin only?
        
        return response

    # Checks request headers for a form of auth and uses to identify the user. Anonymous users are rejected.
    def _authenticate_user():
        logging.debug(f"Inside authenticate user, url: {request.url}")

        # Grab relevant header for auth calls. Ignore other headers
        auth_header = {}
        if "Authorization" in request.headers:
            auth_header["Authorization"] = request.headers["Authorization"]
        elif constants.DOMINO_HEADERS_API_KEY in request.headers:
            auth_header[constants.DOMINO_HEADERS_API_KEY] = request.headers[constants.DOMINO_HEADERS_API_KEY]
        elif constants.DOMINO_PLAY_SESSION_COOKIE in request.cookies:
            auth_header[
                "Cookie"
            ] = f"{constants.DOMINO_PLAY_SESSION_COOKIE}={request.cookies[constants.DOMINO_PLAY_SESSION_COOKIE]}"

        user_response = requests.get(f"{constants.DOMINO_API_HOST}/{constants.WHO_AM_I_ENDPOINT}", headers=auth_header)
        if not user_response.status_code == 200:
            error = "Error getting user"
            logging.error(error)
            return Response(error, 500), {}, None

        user = user_response.json()

        if user["isAnonymous"]:
            warning = "Unable to authenticate user"
            logging.warning(warning)
            return Response(warning, 401)

        return None, auth_header, user

    return app


# gunicorn calls app.run directly, while this is the standard flask wsgi entrypoint for local dev servers
if __name__ == "__main__":
    # gunicorn uses port, but flask has a different default
    PROXY_PORT = os.getenv("FLASK_RUN_PORT", default="8000")

    logging.info("Listening on port " + str(PROXY_PORT))
    create_app().run(port=PROXY_PORT, host="0.0.0.0")