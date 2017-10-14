#!/bin/bash

python manage.py makemigrations --merge --noinput
python manage.py migrate auth
python manage.py migrate api
python manage.py migrate admin
python manage.py migrate django_summernote
python manage.py migrate sessions
python manage.py migrate Event
python manage.py migrate Visitor
python manage.py makemigrations
python manage.py migrate

env

python3 manage.py runserver 0.0.0.0:8000
