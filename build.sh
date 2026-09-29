#!/usr/bin/env bash
set -o errexit
cd django_backend
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
