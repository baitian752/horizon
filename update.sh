#!/bin/bash

echo yes | python manage.py collectstatic
python manage.py compress --force
python manage.py runserver 192.168.56.101:8001
