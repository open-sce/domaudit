import os 
import io
import logging
import dash
import requests
import json
import sys
import urllib

from urllib.parse import urljoin

import dash_bootstrap_components as dbc
import pandas as pd

from dash import Dash, dcc, html, Input, Output, State, callback
from dash import dash_table

from dataclasses import dataclass
from typing import List

DOMAUDIT_VERSION = "1.0"

@dataclass
class Endpoint:
    name: str
    description: str
    endpoint: str
    admin: bool = False

def build_app(app, endpoints: List[Endpoint], base_url):
    
    DOMINO_USER_API_KEY = os.environ.get("DOMINO_USER_API_KEY",None)
    instance_input = dbc.Row(
        [   dbc.Label("DomAudit URL", html_for="instance_url", width=2),
            dbc.Col(
                dbc.Input(
                    type="url", id="instance_url", placeholder="Enter DomAudit Instance URL", value = base_url
                ),
                width=10,
            ),
        ],
        className="mb-3"
    )

    api_input = dbc.Row(
        [
            dbc.Label("Domino User API key", html_for="api-key", width=2),
            dbc.Col(
                dbc.Input(
                    type="password", id="api-key", placeholder="Enter API key", value=DOMINO_USER_API_KEY
                ),
                width=10,
            ),
        ],
        className="mb-3",
    )

    project_input = dbc.Row(
        [
            dbc.Label("Project Name", html_for="project_name", width=2),
            dbc.Col(
                dbc.Input(
                    type="text", id="project_name", placeholder="Enter Domino Project name", value="test"
                ),
                width=10,
            ),
        ],
        className="mb-3",
    )

    project_id_input = dbc.Row(
        [
            dbc.Label("Project ID", html_for="project_id", width=2),
            dbc.Col(
                dbc.Input(
                    type="text", id="project_id", placeholder="Enter Domino Project ID", value="6492f7f37e68fa64ea80f2d9"
                ),
                width=10,
            ),
        ],
        className="mb-3",
    )

    project_owner_input = dbc.Row(
        [
            dbc.Label("Project Owner", html_for="project_owner", width=2),
            dbc.Col(
                dbc.Input(
                    type="text", id="project_owner", placeholder="Enter Project Owner username", value="nmanchev"
                ),
                width=10,
            ),
        ],
        className="mb-3",
    )

    call_options = []
    #option_idx = 0;
    for e in endpoints:
        call_options.append({"label": e.name, "value": e.endpoint, "title": e.description}) #"disabled": not e.admin
        #option_idx += 1


    radio_items = dbc.Row(
        [
            dbc.Label("Audit type", width=2),
            dbc.Col(
                dbc.RadioItems(
                    options = call_options,
                    # Set the first audit type as default
                    value=call_options[0]["value"],
                    id="audit_type",
                ),
                width=10,
            )
        ],
        className="mb-3"
    )


    form = dbc.Form(
        id="form",
        children=[
            instance_input,
            api_input,
            project_owner_input,
            project_input,
            project_id_input,
            radio_items,
            dbc.Button("Submit", id="submit-val")
        ]
    )

    # Set layout
    image_path = "assets/my-image.png"

    header = instance_input = dbc.Row(
        [
            dbc.Col(html.Img(src=dash.get_asset_url("logo.png"), style={"width":"200px"})),
            dbc.Col(html.H2("Domino Audit v" + DOMAUDIT_VERSION))
        ],
        className="mb-3"
    )

    app.layout = html.Div(style={"paddingLeft": "40px", "paddingRight": "40px"}, children=[
        header,
        form,
        html.Br(),
        html.Div(id="output")
    
    ])
 
    @app.callback(
        Output("output", "children"), 
        inputs = [Input("form", "n_submit")],
        state = [State("instance_url", "value"),
        State("api-key", "value"),
        State("project_name", "value"),    
        State("project_id", "value"),    
        State("project_owner", "value"),    
        State("audit_type", "value")],
        prevent_initial_call=True
    )

    def generate_report(n_clicks, instance_url, api_key, project_name, 
                        project_id, project_owner, audit_type):
        try:
            report = project_audit(api_key, instance_url, audit_type, project_name, project_id, project_owner)
        except Exception as e:
            return str(e)

        df = pd.DataFrame.from_dict(report, orient="index", dtype="string")
        df = df.rename_axis("Job ID").reset_index()

        return html.Div(dash_table.DataTable(id="output_table", data = df.to_dict("records"), 
                                            columns = [{"name": str(i), "id": str(i)} for i in df.columns],
                                            style_table={"overflowX": "auto"},
                                            filter_action="native",
                                            sort_action="native",
                                            page_size= 10,
                                            export_format="csv"),
                        className="dbc")
        
def project_audit(auth_token, url, audit_type, project_name, project_id, project_owner):
    
    headers = {"X-Domino-Api-Key":auth_token}

    data = {"project_name": project_name,
            "project_owner": project_owner,
            "project_id": project_id, #"6492f7f37e68fa64ea80f2d91",
            "links":"false"}

    # Prepare API endpoint
    url = url.rstrip("/")
    url += audit_type

    try:
        response = requests.get(url, headers=headers, params=data)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise

    return response.json()

def get_endpoints(base_url):
    logging_level = logging.getLevelName(os.getenv("DOMINO_LOG_LEVEL", "INFO").upper())
    logging.basicConfig(level=logging_level)
    log = logging.getLogger(__name__)

    log.info("Getting API endpoints...")
    url = os.path.join(base_url, "endpoints")
    endpoints = []

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        log.error("Can't get endpoints from {}. Aborting...".format(base_url))
        sys.exit(1)

    for x in response.json()["endpoints"]:
        e = Endpoint(x["name"], x["description"], x["endpoint"], x["admin"])
        log.info("Got endpoint '{}'.".format(e.name))
        endpoints.append(e)

    return endpoints
    
def create_app():

    # Set up logging
    DOMINO_LOG_LEVEL = os.getenv("DOMINO_LOG_LEVEL", "INFO").upper()
    logging_level = logging.getLevelName(DOMINO_LOG_LEVEL)
    logging.basicConfig(level=logging_level)
    log = logging.getLogger(__name__)

    # Get the DomAudit host
    DOMINO_AUDIT_HOST = os.environ.get("DOMINO_AUDIT_HOST")
    if (DOMINO_AUDIT_HOST is None):
        log.error("DOMINO_AUDIT_HOST is not set. Aborting...")
        sys.exit(1)
    else:
        log.info("DOMINO_AUDIT_HOST is set to {}".format(DOMINO_AUDIT_HOST))

    # Get other relevant environment variables
    DOMINO_PROJECT_OWNER = os.environ.get("DOMINO_PROJECT_OWNER")
    DOMINO_PROJECT_NAME = os.environ.get("DOMINO_PROJECT_NAME")
    DOMINO_RUN_ID = os.environ.get("DOMINO_RUN_ID")
    DOMINO_PROXY_PATH = os.environ.get("DOMINO_PROXY_PATH")

    # Check if we are running inside Domino
    if (DOMINO_RUN_ID is not None):
        # We are in Domino
        log.info(f"DOMINO_RUN_ID is {DOMINO_RUN_ID}. We are running inside Domino.")
        DOMINO_USER_API_KEY = os.environ.get("DOMINO_USER_API_KEY")

        # Configure Dash to recognize the URL of the container
        run_url = "/" + DOMINO_PROJECT_OWNER + "/" + DOMINO_PROJECT_NAME + "/r/notebookSession/"+ DOMINO_RUN_ID + "/"
        app = dash.Dash(__name__, routes_pathname_prefix="/", requests_pathname_prefix=run_url, external_stylesheets=[dbc.themes.BOOTSTRAP])
    elif (DOMINO_PROXY_PATH is not None):
        # Running on a proxy path
        log.info(f"DOMINO_PROXY_PATH is {DOMINO_PROXY_PATH}")
        # Configure Dash to recognize the URL of the proxy
        app = dash.Dash(__name__, url_base_pathname=f"/{DOMINO_PROXY_PATH}/", external_stylesheets=[dbc.themes.BOOTSTRAP])

    else:
        log.info("DOMINO_RUN_ID is None. The app has been deployed outside of Domino.")
        app = dash.Dash(__name__, routes_pathname_prefix='/', external_stylesheets=[dbc.themes.BOOTSTRAP])

    endpoints = get_endpoints(DOMINO_AUDIT_HOST)
    build_app(app, endpoints, DOMINO_AUDIT_HOST)
    return app.server

if __name__ == "__main__":
    UI_PORT = os.getenv("UI_PORT",8888)
    create_app().run(port=UI_PORT, host='0.0.0.0', debug=True)
