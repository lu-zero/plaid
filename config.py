import os


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # Flask
    SECRET_KEY = '123456790'
    # cross-site request forgery prevention
    CSRF_ENABLED = True

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')

    # Flask-Mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = None

    # Flask-User
    USER_ENABLE_USERNAME = False
    USER_ENABLE_CHANGE_USERNAME = False
    USER_ENABLE_EMAIL = True
    USER_ENABLE_CONFIRM_EMAIL = False
    USER_ENABLE_CHANGE_PASSWORD = True
    USER_ENABLE_FORGOT_PASSWORD = True


configuration = __name__ + '.Config'
