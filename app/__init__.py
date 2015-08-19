from flask import Flask, redirect
from flask.ext.babel import Babel
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import SQLAlchemyUserDatastore
from flask.ext.security import Security, current_user

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

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.models import User, Patch, Role, Submitter, Project, Comment, Series, Topic, Tag


class PlaidModelView(ModelView):

    def is_accessible(self):
        return current_user is not None and current_user.has_role('admin')

admin = Admin(app, name='plaid')
admin.add_view(PlaidModelView(User, db.session))
admin.add_view(PlaidModelView(Role, db.session))
admin.add_view(PlaidModelView(Patch, db.session))
admin.add_view(PlaidModelView(Submitter, db.session))
admin.add_view(PlaidModelView(Project, db.session))
admin.add_view(PlaidModelView(Comment, db.session))
admin.add_view(PlaidModelView(Series, db.session))
admin.add_view(PlaidModelView(Topic, db.session))
admin.add_view(PlaidModelView(Tag, db.session))

user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore,
                    register_form=forms.ExtendedRegisterForm)
