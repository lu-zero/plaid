from flask import Response, Blueprint
from flask import g, render_template, url_for
from flask import request, abort, redirect

from flask.ext import login

from flask.ext.security import current_user, roles_accepted

from app.forms import SearchForm

from app.models import Patch, PatchState
from app.views.decorators import paginable, render, filterable

from app import db

bp = Blueprint('search', __name__, url_prefix='/search')

@bp.route('/')
def index():
    form = SearchForm(request.form)
    return render_template('search.html', form=form)


@bp.route('/query')
@render('search_list.html')
@paginable('patches')
@filterable
def query():
    project = request.args.get('project', None, type=int)
    name = request.args.get('name', None, type=str)
    tags = request.args.getlist('tags')

    query = Patch.query;

    if project:
        query = query.filter_by(project_id=project)

    if name:
        query = query.filter(Patch.name.like('%'+name+'%'))

    if tags:
        query = query.filter(Patch.tags.any(Tag.name.in_(tags)))

    query = query.order_by("Patch.date desc")

    return dict(title="Search", query=query)
