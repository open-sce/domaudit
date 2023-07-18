{{/* vim: set filetype=mustache: */}}

{{/*
Renders full specification for an Ingress object.

If no host is given, then this will just create a path-based routing rule. If a
tls secret is listed, then a tls-termination section will be rendered; a host
name MUST be provided as well. If you define ingress `paths` instead of `path`,
then multiple rules will be created for each path. You MUST define one of these
values.

You can override the default service name and port by adding the values
"overrideName" and "overridePort", respectively, to the context passed to this
macro.

Expected values: `ingress.path` or `ingress.paths`
Optional values: `ingress.annotations`, `ingress.hosts`, `ingress.host` and `ingress.tlsSecret`
*/}}
{{- define "common.ingress.fullspec" -}}
{{- if not .Values.ingress.paths -}}
{{- $_ := required ".Values.ingress.paths or .Values.ingress.path is required!" .Values.ingress.path -}}
{{- end -}}

{{- $ingressPaths := or .Values.ingress.paths (compact (list .Values.ingress.path)) -}}
{{- $ingressHosts := or .Values.ingress.hosts (compact (list .Values.ingress.host)) -}}
{{- $serviceName := default (include "domaudit.fullname" .) .overrideName -}}
{{- $servicePort := default "http" .Values.service.port -}}

{{- with .Values.ingress.tlsSecret }}
tls:
- hosts:
  {{- if not $ingressHosts -}}
  {{- fail ".Values.ingress.host or .hosts is required!" -}}
  {{- end -}}

  {{- range $_, $host := $ingressHosts }}
  - {{ $host | quote }}
  {{- end }}
  secretName: {{ . }}
{{- end }}

rules:
{{- range $_, $path := $ingressPaths }}
  {{- if $ingressHosts }}
  {{- range $_, $host := $ingressHosts }}
  - host: {{ $host | quote }}
    http:
      paths:
      - path: /{{ $path }}/?(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: {{ $serviceName }}
            port: 
              number: {{ int $servicePort }}
  {{- end }}
  {{- else }}
  - http:
      paths:
      - path: /{{ $path }}/?(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: {{ $serviceName }}
            port: 
              number: {{ int $servicePort }}
  {{- end }}
{{- end }}


{{- end -}}

{{- define "common.ingress.istioAnnotations" -}}
{{- if $.Values.istio.enabled }}
nginx.ingress.kubernetes.io/service-upstream: "true"
nginx.ingress.kubernetes.io/upstream-vhost: {{ include "domaudit.fullname" $ }}.{{ .Release.Namespace }}.svc.{{ .Values.clusterDomain }}
{{- end }}
{{- end }}

{{- define "common.ingress.uiistioAnnotations" -}}
{{- if $.Values.istio.enabled }}
nginx.ingress.kubernetes.io/service-upstream: "true"
nginx.ingress.kubernetes.io/upstream-vhost: {{ include "domaudit.fullname" $ }}-ui.{{ .Release.Namespace }}.svc.{{ .Values.clusterDomain }}
{{- end }}
{{- end }}


{{- define "common.ingress.uifullspec" -}}
{{- if not .Values.ui.ingress.paths -}}
{{- $_ := required ".Values.ui.ingress.paths or .Values.ui.ingress.path is required!" .Values.ui.ingress.path -}}
{{- end -}}

{{- $ingressPaths := or .Values.ui.ingress.paths (compact (list .Values.ui.ingress.path)) -}}
{{- $ingressHosts := or .Values.ui.ingress.hosts (compact (list .Values.ui.ingress.host)) -}}
{{- $serviceName := default (include "domaudit.fullname" .) .overrideName -}}
{{- $servicePort := default "http" .Values.ui.service.port -}}

{{- with .Values.ui.ingress.tlsSecret }}
tls:
- hosts:
  {{- if not $ingressHosts -}}
  {{- fail ".Values.ui.ingress.host or .hosts is required!" -}}
  {{- end -}}

  {{- range $_, $host := $ingressHosts }}
  - {{ $host | quote }}
  {{- end }}
  secretName: {{ . }}
{{- end }}

rules:
{{- range $_, $path := $ingressPaths }}
  {{- if $ingressHosts }}
  {{- range $_, $host := $ingressHosts }}
  - host: {{ $host | quote }}
    http:
      paths:
      - path: /{{ $path }}/?(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: {{ $serviceName }}-ui
            port: 
              number: {{ int $servicePort }}
  {{- end }}
  {{- else }}
  - http:
      paths:
      - path: /{{ $path }}/?(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: {{ $serviceName }}-ui
            port: 
              number: {{ int $servicePort }}
  {{- end }}
{{- end }}


{{- end -}}