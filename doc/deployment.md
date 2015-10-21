# Setup and Deploy Plaid

## Requirements
Plaid requires a database that sqlalchemy can access and some Flask dependencies, the easiest way
to set it up is using a virtual environment

    virtualenv --no-site-packages .venv
    source .venv/bin/activate

    pip install -r requirements.txt

By default plaid uses a sqlite database.

## Initial setup
Currently plaid is unreleased the suggested setup for testing it uses directly git

    git clone git://github.com/lu-zero/plaid.git
    cd plaid
    git checkout deploy
    vim config.py
    git commit -a "Initial config"


    python manage.py db init
    python manage.py db migrate
    python manage.py db upgrade

    python manage.py user create -n admin -e admin@admin.com -p admin -r admin
    python manage.py project create -n projectname -l listname -i list.identifier.org -d "Description"

## Update

    git fetch
    git rebase origin/master
    python manage.py db migrate
    python manage.py db upgrade

## Deploy

uswgi+nginx is the suggested setup for the web component.
The importer can be run as a cronjob or as a mailhook, postfix is the suggested mailserver.

### nginx
Plaid by default assumes to be mounted at the root of your domain (e.g. plaid.yourhost.tld)

```
    location / {
        include "uwsgi_params";
        uwsgi_modifier1 30;

        if (!-f $request_filename) {
            uwsgi_pass localhost:1236;
        }
    }
```


If you need to mount plaid as a `yourhost.tld/plaid` use the following

```
    location /plaid {
        include "uwsgi_params";
        uwsgi_param SCRIPT_NAME /plaid;
        uwsgi_modifier1 30;

        if (!-f $request_filename) {
            uwsgi_pass localhost:1236;
        }
    }
```

### uwsgi
A simple way to test plaid is to run the following from the plaid root

    uwsgi --plugin python27 --socket localhost:1236 -H /home/plaid/plaid/.venv --module app --callable app

If you prefer to use a `ini` file:

``` ini
[uwsgi]
chdir = /home/plaid/plaid/
home = /home/plaid/plaid/.venv
socket = localhost:1236
gid  = 1236
uid  = 1236
module = app
callable = app
```

### postfix
Assuming you created a plaid@yourhost.tld, edit your `master.cf

```
plaid   unix  -       n       n       -       -       pipe
  flags=FR user=plaid argv=/home/plaid/postfix-to-plaid.sh
  ${nexthop} ${user}
```

`postfix-to-plaid.sh` is a simple wrapper that activates the virtualenv and runs

    python manage.py import

