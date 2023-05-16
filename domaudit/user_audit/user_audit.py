import logging
from keycloak import KeycloakAdmin
from keycloak.keycloak_admin import KeycloakAdmin
from keycloak.urls_patterns import URL_ADMIN_EVENTS
from os import getenv
from flask import jsonify
from datetime import datetime


logger = logging.getLogger(__name__)

# Get Keycloak user event data, using env variables for login
# Parameters:
#   username: Optional Domino username to filter for audits
#   dateFrom/dateTo: Optional date filters (yyyy-MM-dd format)
#   type: Optional event type(s) filter

# TODO: Capture downstream KC errors and return them via api response
# TODO: Allow filter by email

def get_user_events(data=None):

    keycloak_server = f'http://{getenv("KEYCLOAK_HOST")}/auth/'
    keycloak_user = getenv("KEYCLOAK_USERNAME","keycloak")
    keycloak_pwd = getenv("KEYCLOAK_PASSWORD")
    if data:
        args = dict(data)
    else:
        args = dict()
    
    logging.info(f"Connecting to keycloak at {keycloak_server}, parameters: {args}")
    
    keycloak_admin = KeycloakAdmin(                            
                            server_url=keycloak_server,
                            username=keycloak_user,
                            password=keycloak_pwd,
                            realm_name="DominoRealm",
                            user_realm_name="master",
                            verify=True)

    users_list = keycloak_admin.get_users()
    all_users = dict()
    for user in users_list:
        all_users[user['id']] = {"username" : user['username'], "email" : user['email']}

    if 'username' in args:
        for user in users_list:
            if user.get('username',None) == args['username']:
                del args['username']
                args["user"] = user['id']
                break
    
    # We need to do this because python-keycloak's get_events
    #  does not support pagination, so we call the __fetch_all
    #  class method directly

    path = {"realm-name": keycloak_admin.realm_name}
    events = keycloak_admin._KeycloakAdmin__fetch_all(URL_ADMIN_EVENTS.format(**path),args)

    response = {}
    for event in events:
        time = event.get("time", None)
        response[time] = {}
        clean_time = datetime.utcfromtimestamp(
                event.get("time", 0)/1000.0
            ).strftime(
                '%Y-%m-%d %H:%M:%S.%f'
            )
        if 'userId' in event:
            user = all_users.get(event.get("userId" ,None))
        else:
            user = None
        response[time]["time"] = clean_time,
        response[time]["type"] = event.get("type", None),
        response[time]["keycloakUserId"] = event.get('userId',None),
        response[time]["ipAddress"] = event.get("ipAddress", None),
        response[time]["username"] = user.get("username", None) if user else "",
        response[time]["email"] = user.get("email", None) if user else ""

    return response

if __name__ == "__main__":
    get_user_events()
    #get_user_events({"username" : "vaibhav_dhawan"})
    