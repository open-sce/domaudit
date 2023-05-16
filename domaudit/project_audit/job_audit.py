import os
import logging
import requests
import datetime
from joblib import Parallel, delayed
from domaudit.services import constants

api_host = os.getenv('DOMINO_API_HOST')

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

def api_fail(status_code, origin):
    """
    Error message for if we don't get the expected htp code
    """
    logging.error(f"An API error has occured whilst running {origin}. Status code: {status_code}")
    exit(1)


def get_project_id(project_name, project_owner, auth_header):
    """
    Returns if of a project
    """
    url = f"{api_host}/{constants.GATEWAY_ENDPOINT}/projects/findProjectByOwnerAndName"
    params = {"ownerName": project_owner,
              "projectName": project_name }
    result = requests.get(url, params=params, headers=auth_header)
    if result.status_code != 200:
        api_fail(result.status_code, "get_project_owner")
    project_id = result.json().get("id", None)
    return project_id    


def get_project_owner(project_id, auth_header):
    """
    Returns username of the owner of a project
    """
    url = f"{api_host}/{constants.GET_PROJECTS_ENDPOINT}/{project_id}"
    result = requests.get(url, headers=auth_header)
    if result.status_code != 200:
        api_fail(result.status_code, "get_project_owner")
    owner_username = result.json().get("ownerUsername", None)
    return owner_username


def get_jobs(project_id, auth_header):
    """
    This will return a list of all job IDs from the selected project.
    """
    url = f"{api_host}/{constants.JOBS_ENDPOINT}?projectId={project_id}&page_size=1000&show_archived=true"
    result = requests.get(url, headers=auth_header)
    if result.status_code != 200:
        api_fail(result.status_code, "get_jobs")
    jobs = result.json().get("jobs", None)
    job_ids = []
    for job in jobs:
        job_ids.append(job.get("id", None))
    return job_ids


def get_job_data(job_id, auth_header):
    endpoints = [f"/{constants.JOBS_ENDPOINT}/{job_id}",
                 f"/{constants.JOBS_ENDPOINT}/{job_id}/runtimeExecutionDetails",
                 f"/{constants.JOBS_ENDPOINT}/{job_id}/comments",
                 f"/{constants.JOBS_ENDPOINT}/job/{job_id}/artifactsInfo"]
    job_data = {}
    for endpoint in endpoints:
        url = f"{api_host}{endpoint}"
        result = requests.get(url, headers=auth_header)
        if result.status_code != 200:
            api_fail(result.status_code, "get_job_data")
        if result.json() is not None:
            job_data.update(result.json())
    return job_data


def get_goals(project_id, auth_header):
    url = f"{api_host}/{constants.PROJECTMANAGEMENT_ENDPOINT}/{project_id}/goals"
    result = requests.get(url, headers=auth_header)
    if result.status_code != 200:
        api_fail(result.status_code, "get_goals")
    goals = {}
    for goal in result.json():
        goals[goal.get("id", None)] = goal.get("title", None)
    return goals


def aggregate_job_data(job_ids, auth_header, threads):
    jobs = {}
    def process(job_id):
        return get_job_data(job_id, auth_header)
    result = Parallel(n_jobs=threads)(delayed(process)(job_id) for job_id in job_ids)
    for job in result:
        jobs[job.get("id", None)] = job
    return jobs


def convert_datetime(time_str):
    return datetime.datetime.fromtimestamp(time_str / 1e3, tz=datetime.timezone.utc).strftime('%F %X:%f %Z')


def generate_report(jobs, goals, project_name, project_owner, project_id):
    tidy_jobs = {}
    for job in jobs:
        tidy_jobs[job] = {}
        comments = []
        if jobs.get(job, None).get("comments", None):
            for comment_details in jobs.get(job, None).get("comments", '[]'):
                comment = {
                    'comment-username': comment_details.get("commenter", None).get("username", None),
                    'comment-timestamp': convert_datetime(comment_details.get("created", 0)),
                    'comment-value': comment_details.get("commentBody", None).get("value", None)
                }
                comments.append(comment)
        tidy_jobs[job]['Comments'] = comments
        git_repos = []
        if jobs.get(job, None).get("dependentRepositories", None):
            for repo in jobs.get(job, None).get("dependentRepositories", '[]'):
                repo_uri = repo.get("uri", None)
                git_repos.append(repo_uri)
        tidy_jobs[job]['Linked Repos'] = git_repos
        dataset_names = []
        if jobs.get(job, None).get("dependentDatasetMounts", None):
            for dataset in jobs.get(job, None).get("dependentDatasetMounts", '[]'):
                dataset_name = dataset.get("datasetName", None)
                dataset_names.append(dataset_name)
        tidy_jobs[job]['Datasets'] = dataset_names
        goal_names = []
        if jobs.get(job, None).get("goalIds", None):
            for goal_id in jobs.get(job, None).get("goalIds", '[]'):
                goal_names.append(goals[goal_id])
        tidy_jobs[job]['Goals'] = goal_names        
        tidy_jobs[job]['Project Name'] = project_name
        endStateCommit = jobs.get(job, None).get("endState", None).get("commitId", None)
        commit_url = f"{api_host}/u/{project_owner}/{project_name}/browse?commitId={endStateCommit}"
        tidy_jobs[job]["Results Commit URL"] = commit_url
        audit_url = f"{api_host}/projects/{project_id}/auditLog"
        tidy_jobs[job]["Audit URL"] = audit_url
        tidy_jobs[job]["Command"] = jobs.get(job, None).get("jobRunCommand", None)
        tidy_jobs[job]["Hardware Tier"] = jobs.get(job, None).get("hardwareTier", None)
        tidy_jobs[job]["Username"] = jobs.get(job, None).get("startedBy", None).get("username", None)
        tidy_jobs[job]["Execution Status"] = jobs.get(job, None).get("statuses", None).get("executionStatus", None)
        tidy_jobs[job]["Submission Time"] = convert_datetime(jobs.get(job, 0).get("stageTime", 0).get("submissionTime", 0))
        if jobs.get(job, None).get("stageTime", None).get("runStartTime", None):
            tidy_jobs[job]["Run Start Time"] = convert_datetime(jobs.get(job, 0).get("stageTime", 0).get("runStartTime", 0))
        else:
            tidy_jobs[job]["Run Start Time"] = None
        tidy_jobs[job]["Completed Time"] = convert_datetime(jobs.get(job, 0).get("stageTime", 0).get("completedTime", 0))
        tidy_jobs[job]["Environment Name"] = jobs.get(job, None).get("environment", None).get("environmentName", None)
        tidy_jobs[job]["Environment Version"] = jobs.get(job, None).get("environment", None).get("revisionNumber", None)
        tidy_jobs[job]["Execution Status Completed"] = jobs.get(job, None).get("statuses", None).get("isCompleted", None)
        tidy_jobs[job]["Execution Status Archived"] = jobs.get(job, None).get("statuses", None).get("isArchived", None)
        tidy_jobs[job]["Execution Status Scheduled"] = jobs.get(job, None).get("statuses", None).get("isScheduled", None)
    return tidy_jobs


def main(auth_header, requesting_user, args=None):
    t0 = datetime.datetime.now()
    if not all(key in args for key in ("project_name","project_owner","project_id")):
        logging.error(f"No project details have been supplied. Args sent: {args}")
        error = {
            "message": "Usage: /project_audit?project_name=<project_name>&project_owner=<project_owner>&project_id=<project_id>"
        }
        return error
    project_id = args.get('project_id', None)
    project_name = args.get('project_name', None)
    project_owner = args.get('project_owner', None)
    # threads = int(args.get('threads', 1))
    threads = os.getenv("PROJECT_AUDIT_WORKER_THREAD_COUNT",1)
    logging.info(f"Args sent: {args}")
    logging.info(f"{requesting_user} requested audit report for {project_name}...")
    goals = get_goals(project_id, auth_header)
    job_ids = get_jobs(project_id, auth_header)
    logging.info(f"Found {len(job_ids)} jobs to report. Aggregating job metadata...")
    logging.info(f"Attempting API queries using {threads} thread(s)...")
    t = datetime.datetime.now()    
    jobs = aggregate_job_data(job_ids, auth_header, threads=threads)
    t = datetime.datetime.now() - t
    logging.info(f"Queries succeeded in {str(round(t.total_seconds(),1))} seconds.")     
    report_data = generate_report(jobs,goals,project_name, project_owner, project_id)
    logging.info(f"Audit report generated in {str(round(t.total_seconds(),1))} seconds.")
    return report_data


if __name__ == '__main__':
    main()