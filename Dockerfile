FROM quay.io/domino/python-slim:3.10.10-slim-bullseye-356295
ENV PATH=$PATH:/app/.local/bin:/app/bin
ENV PYTHONUNBUFFERED=true
ENV FLASK_ENV=production
ENV LOG_LEVEL=WARNING
ENV PYTHONPATH=/app

RUN groupadd --gid 1000 domino && \
    useradd --uid 1000 --gid 1000 domino -m -d /app

RUN apt-get update \
    && apt-get upgrade --yes \
    && apt-get install -y --no-install-suggests --no-install-recommends \
        curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER domino
ADD requirements.txt .
RUN pip install --user -r requirements.txt

COPY --chown=domino:domino domaudit /app/domaudit


