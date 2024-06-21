FROM cgr.dev/dominodatalab.com/python:3.11.9-dev AS builder
USER root
WORKDIR /app
RUN addgroup --system --gid 1000 domino && \
    adduser --system \
    -h / \
    -H \
    -u 1000 \
    -G domino \
    -D \
    domino

RUN apk update && apk add --no-cache build-base postgresql-dev

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM cgr.dev/dominodatalab.com/python@sha256:31ccc46660f85249114a2df0697a3f8606326a427704a003bac9efd0051160c0 AS final

ENV PYTHONPATH "${PYTHONPATH}:/usr/lib/python3.11/site-packages/"
ENV PATH=$PATH:/usr/local/bin
ENV PYTHONUNBUFFERED=true
ENV PYTHONUSERBASE=/home/app
ENV FLASK_DEBUG=false
ENV LOG_LEVEL=INFO
ENV GUNICORN_CMD_ARGS="--timeout 1200 --worker-class gevent --workers 3 --config=/usr/local/bin/gunicorn-gevent.conf.py --chdir /app -b 0.0.0.0"

USER root

# Copy files from builder to the final image
COPY --from=builder \
    /etc/passwd \
    /etc/group \
    /etc/shadow \
    /etc/
COPY --from=builder /usr/lib/python3.11/site-packages/ /usr/lib/python3.11/site-packages
COPY --from=builder /usr/bin/gunicorn /usr/local/bin/gunicorn
COPY --from=builder /usr/lib/libpq.so.* /usr/lib/
USER 1000
WORKDIR /app


COPY --chown=domino domaudit /app/domaudit
COPY --chown=domsed domaudit_ui /app/domaudit_ui
COPY --chown=domino gunicorn-gevent.conf.py /usr/local/bin/gunicorn-gevent.conf.py

USER domino