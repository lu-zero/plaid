from flask import Flask
from flask.ext.babel import Babel
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.user import SQLAlchemyAdapter
from flask.ext.user import UserManager

from config import configuration


app = Flask(__name__)
app.config.from_object(configuration)
try:
    app.config.from_object('local_settings')
except:
    pass
babel = Babel(app)
mail = Mail(app)
db = SQLAlchemy(app)


from app import render
from app import views
from app import models


db_adapter = SQLAlchemyAdapter(db, models.User)
user_manager = UserManager(db_adapter, app)
