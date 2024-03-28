import requests
from os import getenv, path
import sys
import argparse
import time
import pandas as pd 

DOM_NAMESPACE = getenv("DOMINO_API_HOST").split(".")[1].split(":")[0]
DOMAUDIT_HOST = getenv("DOMAUDIT_HOST",f"http://domaudit.{DOM_NAMESPACE}")
USER_AUDIT_PATH = "/user_audit"
PROJECT_AUDIT_PATH = "/project_audit"
PROJECT_ACTIVITY_PATH = "/project_activity"

def get_project_id(project_owner, project_name):

    project = make_call(f"{getenv('DOMINO_API_HOST')}/v4/gateway/projects/findProjectByOwnerAndName",
              {"ownerName": project_owner, "projectName": project_name} )
    
    return project['id']

def make_call(host,parameters=None):

    headers = {"X-Domino-Api-Key": getenv("DOMINO_USER_API_KEY")}
    response = requests.get(host, params=parameters, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error when making request : {response.text}")
        raise Exception(response.text)

def write_file(prefix, data, path, output):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    df = pd.DataFrame.from_dict(data, orient='index')
    if output == "csv":
        filename = f"{prefix}-{timestr}.csv"
        df.to_csv(f"{path}/{filename}", header=True, index=False)
    elif output == "json":
        filename = f"{prefix}-{timestr}.json"
        df.to_json(f"{path}/{filename}", orient="records")
    elif output == "excel":
        filename = f"{prefix}-{timestr}.xlsx"
        df.to_excel(f"{path}/{filename}",header=True, index=False)
    
    print(f"{prefix} Output written to {path}/{filename}")

def cli():       
    parser = argparse.ArgumentParser(
                        description='Field solution for extending Domino Audit capabilities')

    parser.add_argument("--host", help=f"Domaudit service host - optional, defaults to {DOMAUDIT_HOST}", default=DOMAUDIT_HOST)
    parser.add_argument("--output-type", help=f"Output Type. Defaults to csv, options are : csv, excel, json", default="csv")
    parser.add_argument("--output-path", help=f"Output path. Defaults to local directory", default="./")


    subparsers = parser.add_subparsers(title="Audits",required=True, dest="audit")
    user_parser = subparsers.add_parser(name="user", help="User Audit. Defaults to all rows, user --first/--last to request paginated data")
    user_parser.add_argument("--username", help="Domino username to filter audit records")
    user_parser.add_argument("--type", help="Event type to filter on")
    user_parser.add_argument("--date-from", help="Start date for filter - YYYY-MM-DD format",dest="dateFrom")
    user_parser.add_argument("--date-to", help="End date for filter - YYYY-MM-DD format", dest="dateTo")
    user_parser.add_argument("--first", help="Start index for paginated requests (optional)",dest="first")
    user_parser.add_argument("--last", help="End index for paginated requests (optional)", dest="max")

    project_parser = subparsers.add_parser(name="project", help="Project Audit")
    project_parser.add_argument("--project", help="Domino Project to audit, in the format OWNER/PROJECT", 
                                default="/".join([getenv("DOMINO_PROJECT_OWNER"),getenv("DOMINO_PROJECT_NAME")]))
    project_parser.add_argument("--links", action=argparse.BooleanOptionalAction, help="Include links back to Domino", default=False)
    project_parser.add_argument("--page-size", help="Page size of returned jobs, default 1000", default=1000)
    project_parser.add_argument("--page-number", help="Page number to return, default 1", default=1)

    activity_parser = subparsers.add_parser(name="activity", help="Project Activity")
    activity_parser.add_argument("--project", help="Domino Project to audit, in the format OWNER/PROJECT", 
                                default="/".join([getenv("DOMINO_PROJECT_OWNER"),getenv("DOMINO_PROJECT_NAME")]))
    activity_parser.add_argument("--page-size", help="Maximum number of rows returned. Default is 500", default="500")
    activity_parser.add_argument("--latest-event-time", help="End date of the activity report - YYYY-MM-DD format")
    activity_parser.add_argument("--activity-source", help="Filter by activity source. Valid values: \n\t"
                                "project, job, model_api, schedule_job, files, workspace, comment, app")


    if len(sys.argv) <= 1:
        parser.print_help()
        exit(1)
    args = parser.parse_args()

    output_type = args.output_type
    output_path = args.output_path

    if output_type not in ["csv","json","excel"]:
        print(f"Invalid Output type: {output_type}")
        parser.print_help()
        exit(1)

    if not path.exists(path.dirname(output_path)):
        print(f"Output directory {output_path} does not exist")
        exit(1)

    clean_args = args.__dict__.copy()
    clean_args.pop("host")
    clean_args.pop("audit")
    clean_args.pop("output_type")
    clean_args.pop("output_path")

    if args.audit == "user":
        output = make_call(f"{DOMAUDIT_HOST}{USER_AUDIT_PATH}",clean_args)
    elif args.audit == "project":
        split_string = args.project.split("/")
        if len(split_string)==2:
            project_owner = split_string[0]
            project_name = split_string[1]
            project_id = get_project_id(project_owner,project_name)
            links = args.links
        else:
            print(f"Invalid project name format: {args.project}")
            project_parser.print_help()
            exit(1)

        project_args = {
            "project_id": project_id,
            "project_name": project_name,
            "project_owner": project_owner,
            "links": links,
            "page_size": args.page_size,
            "page_number": args.page_number,
        }
        output = make_call(f"{DOMAUDIT_HOST}{PROJECT_AUDIT_PATH}",project_args)
    elif args.audit == "activity":
        split_string = args.project.split("/")
        if len(split_string)==2:
            project_owner = split_string[0]
            project_name = split_string[1]
            project_id = get_project_id(project_owner,project_name)
        else:
            print(f"Invalid project name format: {args.project}")
            activity_parser.print_help()
            exit(1)

        activity_args = {
            "project_id": project_id,
            "page_size": args.page_size,
            "latest_event_time": args.latest_event_time,
            "activity_source": args.activity_source
        }
        print(f"*** Only returning the first {args.page_size} activities by date descending ***")
        output = make_call(f"{DOMAUDIT_HOST}{PROJECT_ACTIVITY_PATH}",activity_args)


    write_file(args.audit, output, output_path, output_type)


if __name__ == "__main__":
    cli()
