from flask import Flask
from flask.ext.babel import Babel
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import SQLAlchemyUserDatastore
from flask.ext.security import Security

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


from app import forms
from app import models
from app import render
from app import views


user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore,
                    register_form=forms.ExtendedRegisterForm)
