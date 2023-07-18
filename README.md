# Domaudit
## Domino Audit solution

This is a webservice which provides enriched auditing using metadata collected by Domino

This includes 3 endpoints:

- Project Audit: And audit of all jobs run in the project, with all metadata associated with that job.

- Project Activity: An output of the 'Activity' section in the project overview page, with options for filtering

- User Login Audit: An audit log of all user login activities. This endpoint requires an Admin role in domino

---

### Helm installation:

```
helm upgrade --install domaudit helm/domaudit -n domino-platform
```

Optional: enable ingress
```
--set ingress.enabled=true --set ingress.host=xxxx.domino.tech 
```
Required for istio enabled installs
```
--set istio.enabled=true
```
---

### Domaudit CLI

Add the CLI to any domino compute environment to run audits from inside a workspace
```
RUN pip install https://mirrors.domino.tech/domaudit/domaudit_cli-0.0.4-py3-none-any.whl --user
```

In a workspace with the CLI installed, run `domaudit --help` to see a list of available options