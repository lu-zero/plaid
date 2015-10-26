from flask import Response, Blueprint, session
from flask import g, render_template, url_for
from flask import request, abort, redirect
from flask import flash

from flask.ext.login import login_user

import urllib2
import json

from app.models import User
from app.forms import GitHubRegistrationForm

from app import app
from app import github

bp = Blueprint('github', __name__, url_prefix='/auth/github')

@app.before_request
def before_request():
    g.github = True


@bp.route('/register', methods=['GET'])
def register():
    session['github_action'] = 'register'
    return github.authorize(scope='user:email')


@bp.route('/login', methods=['GET'])
def login():
    session['github_action'] = 'login'
    return github.authorize(scope='user:email')


@bp.route('/callback', methods=['GET', 'POST'])
@github.authorized_handler
def callback(access_token):
    if session['github_action'] == 'register':
        return process_github_register(access_token)
    elif session['github_action'] == 'login':
        return process_github_login(access_token)
    else:
        flash('Something is broken with GitHub authentication')
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
        login_user(user)
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
                login_user(user_by_email)
                return redirect('index')

        flash('Unknown GitHub username, please register first')
        return redirect(url_for('github.register'))

    login_user(user_by_github_username)
    return redirect(url_for('index'))
