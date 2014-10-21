plaid
-----

Simple patch tracking system based on Flask. It is similar to the more mature
and featureful [patchwork](http://jk.ozlabs.org/projects/patchwork/), but focuses on
patch series.

Deploy
======

Plaid is written using Flask, so the usual procedure applies:

* Set a virtualenv

```
# virtualenv --no-site-packages venv
# source venv/bin/activate
```

* Install the dependencies
```
# pip install -r requirements.txt
```
* Use `manage.py` to populate the database (use `run_importer.sh` to use the
  test mailbox
```
# python manage.py db init
# python manage.py db migrate
# python manage.py db upgrade
# python manage.py user create -n username -e your@email -p pwd -r admin
# python manage.py project create -n projectname -l listname -i listid -d "Description"
```

* Try locally

```
# python run.py
```
