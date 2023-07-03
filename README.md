# Domaudit
## Domino Audit solution


### Helm installation:

```
helm upgrade --install domaudit helm/domaudit -n domino-platform
```

Optional: enable ingress

`--set ingress.enabled=true --set ingress.host=xxxx.domino.tech `

Required for istio enabled installs

`--set istio.enabled=true`