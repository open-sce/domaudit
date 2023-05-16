import csv
import json
import requests
from os import getenv
import sys
from argparse import ArgumentParser
import time

DOM_NAMESPACE = getenv("DOMINO_API_HOST").split(".")[1].split(":")[0]
DOMAUDIT_HOST = f"http://domaudit.{DOM_NAMESPACE}"
USER_AUDIT_PATH = "/user_audit"
PROJECT_AUDIT_PATH = "/project_audit"

def make_call(host,parameters=None):

    headers = {"X-Domino-Api-Key": getenv("DOMINO_USER_API_KEY")}
    response = requests.get(host, params=parameters, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error when making request : {response.text}")
        raise Exception(response.text)

def write_csv(prefix, json):
    columns = list(set([x for row in json for x in row.keys()]))
    timestr = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{prefix}-{timestr}.csv"

    with open(filename, 'w') as out_file:
        csv_w = csv.writer(out_file)
        csv_w.writerow(columns)
        
        for i_r in json:
            csv_w.writerow(map(lambda x: i_r.get(x, ""), columns))
    
    print(f"{prefix} Output written to {filename}")

def cli():       
    parser = ArgumentParser(
                        description='Field solution for extending Domino Audit capabilities')

    parser.add_argument("--host", help=f"Domaudit service host - optional, defaults to {DOMAUDIT_HOST}", default=DOMAUDIT_HOST)

    subparsers = parser.add_subparsers(title="Audits",required=True, dest="audit")
    user_parser = subparsers.add_parser(name="user", help="User Audit")
    user_parser.add_argument("--username", help="Domino username to filter audit records")
    user_parser.add_argument("--type", help="Event type to filter on")
    user_parser.add_argument("--date-from", help="Start date for filter - YYYY-MM-DD format",dest="dateFrom")
    user_parser.add_argument("--date-to", help="End date for filter - YYYY-MM-DD format", dest="dateTo")

    project_parser = subparsers.add_parser(name="project", help="Project Audit")
    project_parser.add_argument("--project-id", help="Domino Project ID to audit", default=getenv("DOMINO_PROJECT_ID"))
    project_parser.add_argument("--project-name", help="Domino Project name to audit", default=getenv("DOMINO_PROJECT_NAME"))
    project_parser.add_argument("--project-owner", help="Domino Project owner", default=getenv("DOMINO_PROJECT_OWNER"))


    if len(sys.argv) <= 1:
        parser.print_help()
        exit(1)
    args = parser.parse_args()

    clean_args = args.__dict__.copy()
    clean_args.pop("host")
    clean_args.pop("audit")
    print(args)
    if args.audit == "user":
        output = make_call(f"{DOMAUDIT_HOST}{USER_AUDIT_PATH}",clean_args)
    elif args.audit == "project":
        output = make_call(f"{DOMAUDIT_HOST}{PROJECT_AUDIT_PATH}",clean_args)

    write_csv(args.audit, output)


if __name__ == "__main__":
    cli()
