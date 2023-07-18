FROM quay.io/domino/python-slim:3.10.10-slim-bullseye-356295
ENV PATH=$PATH:/app/.local/bin:/app/bin
ENV PYTHONUNBUFFERED=true
ENV FLASK_ENV=production
ENV LOG_LEVEL=INFO
ENV PYTHONPATH=/app
ENV GUNICORN_CMD_ARGS="--timeout 1200 --worker-class gevent --workers 3 --config=/usr/local/bin/gunicorn-gevent.conf.py --chdir /app -b 0.0.0.0"


RUN groupadd --gid 1000 domino && \
    useradd --uid 1000 --gid 1000 domino -m -d /app

RUN apt-get update \
    && apt-get upgrade --yes \
    && apt-get install -y --no-install-suggests --no-install-recommends \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


COPY ./gunicorn-gevent.conf.py /usr/local/bin/gunicorn-gevent.conf.py

COPY domaudit /app/domaudit
COPY domaudit_ui /app/domaudit_ui
USER domino
