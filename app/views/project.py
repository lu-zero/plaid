from flask import Blueprint
from flask import render_template, g
from flask import request, url_for

from app.models import Project, Tag

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


@bp.route('/series/<series_id>')
def series(series_id=None):
    return "TODO"


@bp.route('/admin')
def admin():
    return "TODO"
