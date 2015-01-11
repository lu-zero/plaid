from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from flask.ext import login
from flask.ext.admin import helpers

from app import app
from app import db
from app.forms import LoginForm
from app.forms import RegistrationForm
from app.models import Project
from app.models import User

from . import project, patch

app.register_blueprint(project.bp)
app.register_blueprint(patch.bp)


def redirect_url(default='index'):
    return request.args.get('next') or request.referrer or url_for(default)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',
                           title="Homepage",
                           user=login.current_user,
                           projects=Project.get_all())


@app.route('/login', methods=('GET', 'POST'))
def login_view():
    form = LoginForm(request.form)
    if helpers.validate_form_on_submit(form):
        user = form.get_user()
        if user:
            login.login_user(user, remember=form.remember_me)
            return redirect(request.args.get("next") or url_for("index"))
        else:
            flash('User not found, sorry pal!', 'warning')

    return render_template('login.html',
                           title="Login",
                           user=login.current_user,
                           form=form)


@app.route('/register', methods=('GET', 'POST'))
def register_view():
    form = RegistrationForm(request.form)
    if helpers.validate_form_on_submit(form):
        user = User()
        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        login.login_user(user)
        return redirect(url_for('index'))

    return render_template('register.html', form=form, user=login.current_user,
                           title='Registration')


@app.route('/logout/')
def logout_view():
    login.logout_user()
    return redirect(url_for('index'))
