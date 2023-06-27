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
from domaudit.user_audit.user_audit import get_user_events
from domaudit.project_audit import job_audit

constants.DOMINO_API_HOST = os.getenv("DOMINO_API_HOST", default="http://nucleus-frontend.domino-platform:80")

def create_app(test_config=None):
    logging.getLogger(FLASK_APP_NAME)
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.getLevelName(os.getenv("LOG_LEVEL", default="INFO")),
        datefmt="%H:%M:%S",
    )
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
    
    # @Blake: Do you need this? Its not being set via helm atm
    logging.info(f"Domino Public URI={constants.DOMINO_PUBLIC_URI}")

    # Authentication decorator
    # Checks request headers for a form of auth and uses to identify the user. Anonymous users are rejected.
    # Code stolen shamelessly from mlflow proxy work done by Noah
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
        logging.info(f"Authenticated request for project_audit from {user.get('email', None)}")
        requesting_user = user.get('userName', None)
        result = job_audit.main(auth_header, requesting_user, request.args)
        
        return result

    @app.route("/project_activity", methods=["GET"])
    @authenticate_user
    def get_project_activity(user, auth_header,**kwargs):
        logging.info(f"Authenticated request for project_activity from {user.get('email', None)}")
        requesting_user = user.get('userName', None)
        result = job_audit.get_project_activity(auth_header, requesting_user, request.args)
        
        return result

    @app.route("/user_audit", methods=["GET"])
    @authenticate_admin_user
    def user_audit(user, auth_header,**kwargs):
        logging.debug(f"######## [{request.method}]")
        logging.info(f"Authenticated Admin request for user audit from {user}")
        
        return get_user_events(request.args)


    @app.route("/telemetry_audit", methods=["GET"])
    @authenticate_user
    def telemetry_audit(user, auth_header, **kwargs):
        logging.debug(f"######## [{request.method}]")
        response = {"Hello User": user["fullName"]}
        logging.info(f"Authenticated Telemetry request for user audit from {user}")

        # TODO: get User audit from telemetry records, format as json, return
        # Required input: either user, or project, or both
        # Admin only?
        
        return response


    return app


# gunicorn calls app.run directly, while this is the standard flask wsgi entrypoint for local dev servers
if __name__ == "__main__":
    # gunicorn uses port, but flask has a different default
    PROXY_PORT = os.getenv("FLASK_RUN_PORT", default="8000")

    create_app().run(port=PROXY_PORT, host="0.0.0.0")