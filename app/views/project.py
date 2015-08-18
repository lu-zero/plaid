from flask import Blueprint, Response
from flask import render_template, g
from flask import request, url_for
from flask import redirect

from flask.ext.security import roles_accepted

from app.models import Project, Tag, Series
from app.mbox import mbox

from StringIO import StringIO
from app.models import Patch, PatchState
from app import db

bp = Blueprint('project', __name__, url_prefix='/project/<project_name>')


@bp.url_value_preprocessor
def get_project(endpoint, values):
    project_name = values.pop('project_name')
    g.project = Project.query.filter_by(name=project_name).first_or_404()



@bp.url_defaults
def add_project(endpoint, values):
    if 'project_name' in values or not g.project:
        return
    values['project_name'] = g.project.name


@bp.route('/')
def index():
    return render_template('project.html',
                           title="Project %s" % g.project.name)


@bp.route('/patches/')
@bp.route('/patches/<group>')
@bp.route('/patches/<group>/<int:page>')
def patches(group=None, page=1):
    if group:
        patches = getattr(g.project, group+"_patches", [])
    else:
        group = 'patches'
        patches = g.project.patches

    patches = patches.order_by("Patch.date desc").paginate(page, 50, False)

    def endpoint(page_index):
        return url_for('project.patches', group=group, page=page_index)

    return render_template('project_list.html',
                           title="Project %s" % g.project.name,
                           patches=patches,
                           group=group,
                           endpoint=endpoint)


@bp.route('/tag/')
def tags():
    tags = g.project.tags
    return render_template('tags.html',
                           title="All tags",
                           tags=tags)


@bp.route('/tag/<tag_name>')
@bp.route('/tag/<tag_name>/<int:page>')
def tag(tag_name, page=1):
    tags = g.project.tags

    tag = tags.filter(Tag.name == tag_name).first_or_404()
    patches = tag.patches.filter_by(project_id=g.project.id)

    patches = patches.order_by("Patch.date desc").paginate(page, 50, False)

    def endpoint(page_index):
        return url_for('project.tag', tag_name=tag_name, page=page_index)

    return render_template('tag.html',
                           title="Tag %s" % tag.name,
                           patches=patches,
                           tag=tag,
                           endpoint=endpoint)

@bp.route('/bulk_change_state', methods=['POST'])
@roles_accepted('admin', 'committer')
def bulk_change_state():
    new_state_str = request.form['new_state']
    new_state = PatchState.from_string(new_state_str)
    patches_ids_str = request.form['patches']
    ids = [int(id) for id in patches_ids_str.split(",")]
    for id in ids:
        for p in Patch.query.filter_by(id=id):
            p.state = new_state
    db.session.commit()
    return redirect(request.referrer)

@bp.route('/series/<series_id>')
@bp.route('/series/<series_id>/<int:page>')
def series(series_id, page=1):
    series = Series.query.filter_by(id=series_id).first_or_404()

    patches = series.patches.order_by("Patch.date asc").paginate(page, 50, False)

    def endpoint(page_index):
        return url_for('project.series', series_id=series_id, page=page_index)

    return render_template('series_list.html',
                           title="Series %s" % series.name,
                           series=series,
                           patches=patches,
                           endpoint=endpoint)

@bp.route('/series/<series_id>/mbox')
def series_mbox(series_id):
    series = Series.query.filter_by(id=series_id).first_or_404()
    f = StringIO()
    mb = mbox(f)
    for patch in series.patches.order_by("Patch.date asc"):
        mb.add(patch.mbox)

    return Response(f.getvalue(), mimetype='application/mbox')

@bp.route('/admin')
def admin():
    return "TODO"
