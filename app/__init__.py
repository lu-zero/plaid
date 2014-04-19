from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from flask.ext.login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)

from app import views
from app import models
