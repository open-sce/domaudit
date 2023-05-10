import logging
from keycloak import KeycloakAdmin
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
    
    events = keycloak_admin.get_events(query=args)
    response = []
    for event in events:
        clean_time = datetime.utcfromtimestamp(
                event['time']/1000.0
            ).strftime(
                '%Y-%m-%d %H:%M:%S.%f'
            )
        if 'userId' in event:
            user = all_users.get(event['userId'],None)
        else:
            user = None
        clean_event = {"time": clean_time,
                       "type": event['type'],
                       "keycloakUserId": event.get('userId',''),
                       "ipAddress": event['ipAddress'],
                       "username" : user['username'] if user else "",
                       "email" : user['email'] if user else ""
                       }
        response.append(clean_event)

    
    json_response = jsonify(response)
    return json_response

if __name__ == "__main__":
    get_user_events()
    #get_user_events({"username" : "vaibhav_dhawan"})
    