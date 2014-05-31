#!/bin/sh
# Setup a simple testcase

rm -fR app.db migrations/

python manage.py db init
python manage.py db migrate
python manage.py db upgrade

python manage.py user -n admin -e admin@admin.com -p admin -r admin
python manage.py project -n libav -l libav-devel -i libav-devel.libav.org
python manage.py import --mailbox ./test/data/libav_1_99.mbox
