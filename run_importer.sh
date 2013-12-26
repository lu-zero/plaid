#!/bin/sh
# Setup a simple testcase

python manage.py user -n admin -e admin@admin.com -p admin -r 1
python manage.py project -n libav -l libav-devel -i libav-devel.libav.org
python manage.py import --mailbox ./test/data/libav_1_99.mbox
