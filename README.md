# Domaudit
## Domino Audit solution

This is a webservice which provides enriched auditing using metadata collected by Domino

This includes 3 endpoints:

- Project Audit: And audit of all jobs run in the project, with all metadata associated with that job.

- Project Activity: An output of the 'Activity' section in the project overview page, with options for filtering

- User Login Audit: An audit log of all user login activities. This endpoint requires an Admin role in domino

This service provides 3 ways to request audit reports:
- A CLI, which is designed to run either inside a Domino workspace or externally
- An API endpoint, authorised by your Domino API key
- A web application, deployed as a standalone service

---

### Helm installation:

```
helm upgrade --install domaudit helm/domaudit -n domino-platform
```
<br>  

Optional: enable direct API ingress
```
--set ingress.enabled=true --set ingress.host=xxxx.domino.tech 
```
<br>  

Optional: enable Domaudit webapp
```
--set ui.ingress.enabled=true --set ui.ingress.host=xxxx.domino.tech 
```
<br>  

Required for istio enabled installs
```
--set istio.enabled=true
```
---

### Domaudit CLI

Add the CLI to any domino compute environment to run audits from inside a workspace
```
RUN pip install https://mirrors.domino.tech/domaudit/domaudit_cli-0.0.7-py3-none-any.whl --user
```

In a workspace with the CLI installed, run `domaudit --help` to see a list of available options