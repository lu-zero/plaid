from flask import Response, Blueprint, session
from flask import g, render_template, url_for
from flask import request, abort, redirect
from flask.ext.security import current_user, roles_accepted
from app.forms import ProfileForm, GitHubRegistrationForm
from flask import request, flash

import urllib2
import json

from flask.ext import login
from flask.ext.security.utils import encrypt_password

from app.models import Patch, PatchState, User
from app import app
from app import db
from app import github

bp = Blueprint('user', __name__, url_prefix='/profile')

@app.route('/register_with_github', methods=['GET'])
def register_with_github():
    session['github_action'] = 'register'
    return github.authorize(scope=['user:email'])

@app.route('/login_with_github', methods=['GET'])
def login_with_github():
    session['github_action'] = 'login'
    return github.authorize(scope=['user:email'])


@app.route('/github_callback_register', methods=['GET', 'POST'])
@github.authorized_handler
def github_callback_register(access_token):
    if session['github_action'] == 'register':
        return process_github_register(access_token)
    elif session['github_action'] == 'login':
        return process_github_login(access_token)
    else:
        flash('Somethins is broken with GitHub authentication')
        return redirect(url_for('index'))


def process_github_register(access_token):
    if request.method == 'GET' and access_token is None:
        flash('GitHub authentication failed')
        return redirect(url_for('index'))
    form = GitHubRegistrationForm(request.form)
    if request.method == 'GET' and access_token is not None:
        github_data_str = urllib2.urlopen("https://api.github.com/user?access_token=%s" % access_token).read()
        github_data = json.loads(github_data_str)
        form.email.data = github_data['email']
        form.name.data = github_data['name']

    if request.method == 'POST' and form.validate():
        user = User(name=form.name.data, password=encrypt_password(form.password.data), email=form.email.data)
        db.session.add(user)
        db.session.commit()
        login.login_user(user)
        return redirect('/')
    return render_template('registration_github.html', form=form)


def process_github_login(access_token):
    if access_token is None:
        flash('GitHub authentication failed')
        return redirect(url_for('index'))

    github_data_str = urllib2.urlopen("https://api.github.com/user?access_token=%s" % access_token).read()
    github_data = json.loads(github_data_str)
    email = github_data['email']

    user = User.get_by_email(email)
    if user is None:
        flash('Unknown e-mail, please register first')
        return redirect(url_for('index'))

    login.login_user(user)
    return redirect('/')


@bp.route('/settings', methods=['GET', 'POST'])
def settings():
    form = ProfileForm(request.form, current_user)
    if request.method == 'POST' and form.validate():
        form.populate_obj(current_user)
        current_user.password = encrypt_password(current_user.password)
        db.session.commit()
        return redirect('/')
    else:
        return render_template('profile.html', form=form, profile=current_user)