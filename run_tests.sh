#!/bin/sh

set -e

# the documentation recommends installing the virtualenv in "venv/"
if [ ! -x venv/bin/nosetests ]; then
    virtualenv --no-site-packages venv
    venv/bin/pip install -r requirements.txt
fi

. venv/bin/activate

exec nosetests "$@"
echo "Executing venv/bin/nosetests failed!"
exit 1
