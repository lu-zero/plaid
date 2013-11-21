import os
basedir = os.path.abspath(os.path.dirname(__file__))

# cross-site request forgery prevention
CSRF_ENABLED = True

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
#SQLALCHEMY_DATABASE_URI = 'postgresql://plaid:plaid@localhost/plaid'
SECRET_KEY = '123456790'
