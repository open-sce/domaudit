#!/usr/bin/env python
# config reference at https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py
from psycogreen.gevent import patch_psycopg


# patch forked gevent processes for psycopg2
def post_fork(server, worker):
    # gevent.monkey.patch_all() is already called in GEventWorker for us
    worker.log.info("patching psycopg2 with psycogreen")
    patch_psycopg()

    worker.log.info("patching complete")