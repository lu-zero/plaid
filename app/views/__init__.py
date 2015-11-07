from flask import render_template
from flask import request
from flask import url_for
from flask import g

from flask.ext.security import current_user

from app import app
from app.models import Project

from . import patch
from . import project
from . import user
from . import search

app.register_blueprint(project.bp)
app.register_blueprint(patch.bp)
app.register_blueprint(user.bp)
app.register_blueprint(search.bp)

try:
    from . import github
    app.register_blueprint(github.bp)
except:
    pass

def redirect_url(default='index'):
    return request.args.get('next') or request.referrer or url_for(default)

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html',
                           title="Homepage",
                           user=current_user,
                           projects=Project.get_all())
