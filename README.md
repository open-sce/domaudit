# domaudit
Field Audit Solution

https://onedominodatalab.atlassian.net/browse/PS-7710

Helm installation:


helm upgrade domaudit helm/domaudit -n domino-platform 
# Optional: enable ingress
#  --set ingress.enabled=true --set ingress.host=xxxx.domino.tech 
# Required for istio enabled installs
#  --set istio.enabled=true