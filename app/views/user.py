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
    return github.authorize(scope='user:email')

@app.route('/login_with_github', methods=['GET'])
def login_with_github():
    session['github_action'] = 'login'
    return github.authorize(scope='user:email')


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
        github_user_data = urllib2.urlopen("https://api.github.com/user?access_token=%s" % access_token).read()
        github_user = json.loads(github_user_data)
        github_emails_data = urllib2.urlopen("https://api.github.com/user/emails?access_token=%s" % access_token).read()
        github_emails = json.loads(github_emails_data)

        form.email.data = github_emails[0]['email']
        form.name.data = github_user['name']
        form.github_username.data = github_user['login']

    if request.method == 'POST' and form.validate():
        user = User(name=form.name.data, password=encrypt_password(form.password.data), email=form.email.data, github_username=form.github_username.data)
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
    github_username = github_data['login']

    user_by_github_username = User.get_by_github_username(github_username)
    if user_by_github_username is None:

        # If this user has already registered normally we can just associate to the plaid user the
        # github username. To do so we look among e-mails
        github_emails_data = urllib2.urlopen("https://api.github.com/user/emails?access_token=%s" % access_token).read()
        github_emails = json.loads(github_emails_data)
        for entry in github_emails:
            email = entry['email']
            user_by_email = User.get_by_email(email)
            if user_by_email:
                flash("Associating '%s' to GitHub user '%s'" % (user_by_email.name, github_username))
                user_by_email.github_username = github_username
                db.session.commit()
                login.login_user(user_by_email)
                return redirect('/')

        flash('Unknown GitHub username, please register first')
        return redirect(url_for('register_with_github'))

    login.login_user(user_by_github_username)
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
