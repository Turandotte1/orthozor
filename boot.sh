#!/bin/sh

. venv/bin/activate
flask db upgrade
exec gunicorn -w 6 -b :5000 --access-logfile - --error-logfile - wsgi:app