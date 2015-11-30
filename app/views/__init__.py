from flask import render_template
from flask import request
from flask import url_for
from flask import g

from flask.ext.security import current_user
from flask.ext.security import roles_accepted

from app import app
from app.models import Project
from app.models import Patch

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


@app.route('/bulk_update', methods=['POST'])
@roles_accepted('admin', 'committer')
def bulk_update():
    new_state_str = request.form['new_state']
    new_state = PatchState.from_string(new_state_str)
    patches_ids_str = request.form['patches']
    ids = [int(id) for id in patches_ids_str.split(",")]
    for id in ids:
        for p in Patch.query.filter_by(id=id):
            p.state = new_state
    db.session.commit()
    return redirect(request.referrer)
