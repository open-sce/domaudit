import json
import sys
import os
import logging

from flask import Flask, request, Response
from flask_healthz import Healthz
import requests
from domaudit.services import constants
from domaudit import FLASK_APP_NAME
from functools import wraps, partial
from domaudit.project_audit import audit

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
                "live": "domaudit.services.health.check_liveness",
                "ready": "domaudit.services.health.check_readiness",
            },
        }
    )

    Healthz(app, no_log=True)

    logging.info("Starting up Field Audit API service")
    logging.info("Domino Nucleus URI=" + constants.DOMINO_API_HOST)
    logging.info(f"Domino Public URI={constants.DOMINO_PUBLIC_URI}")

    # Authentication decorator
    # Checks request headers for a form of auth and uses to identify the user. Anonymous users are rejected.
    def _authenticate_user(f, is_admin):
        @wraps(f)
        def authenticate(*args, **kwargs):
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
            else:
                return Response("No Auth info provided, this endpoint requires authentication", 401)

            user_response = requests.get(f"{constants.DOMINO_API_HOST}/{constants.WHO_AM_I_ENDPOINT}", headers=auth_header)
            if not user_response.status_code == 200:
                error = "Error getting user: {user_response.text}"
                logging.error(error)
                return Response(error, 500), {}, None

            user = user_response.json()

            if user["isAnonymous"]:
                warning = "Unable to authenticate user"
                logging.warning(warning)
                return Response(warning, 401)
            
            if is_admin and not user['isAdmin']:
                warning = "Endpoint requires Admin Domino access"
                logging.warning(warning)
                return Response(warning, 401)
            
            user_self = requests.get(f"{constants.DOMINO_API_HOST}/{constants.USER_ENDPOINT}", headers=auth_header).json()

            return f(user_self, auth_header,*args, **kwargs)
        return authenticate

    authenticate_user = partial(_authenticate_user,is_admin=False)
    authenticate_admin_user = partial(_authenticate_user,is_admin=True)

    @app.route("/project_audit", methods=["GET"])
    @authenticate_user
    def project_audit(user, auth_header,**kwargs):
        logging.debug(f"######## [{request.method}]")
        response = {"Hello User": user["fullName"]}
        blake = audit.main(auth_header)
        # TODO: get project audit, format as json, return
        # Validate user has access to project
        
        return blake

    @app.route("/user_audit", methods=["GET"])
    @authenticate_admin_user
    def user_audit(user, auth_header,**kwargs):
        logging.debug(f"######## [{request.method}]")
        response = {"Hello Admin" : user["fullName"]}

        # TODO: get User audit from keycloak, format as json, return
        # Optional time frame input. Default 30(?) days
        # Admin only
        
        return response

    @app.route("/telemetry_audit", methods=["GET"])
    @authenticate_user
    def telemetry_audit(user, auth_header, **kwargs):
        logging.debug(f"######## [{request.method}]")
        response = {"Hello User": user["fullName"]}

        # TODO: get User audit from telemetry records, format as json, return
        # Required input: either user, or project, or both
        # Admin only?
        
        return response


    return app


# gunicorn calls app.run directly, while this is the standard flask wsgi entrypoint for local dev servers
if __name__ == "__main__":
    # gunicorn uses port, but flask has a different default
    PROXY_PORT = os.getenv("FLASK_RUN_PORT", default="8000")

    logging.info("Listening on port " + str(PROXY_PORT))
    create_app().run(port=PROXY_PORT, host="0.0.0.0")