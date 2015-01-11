from flask import Blueprint
from flask import g

from app.models import Series

bp = Blueprint('series', __name__, url_prefix='/series/<series_id>')


@bp.url_value_preprocessor
def get_series(endpoint, values):
    series_id = values.pop('series_id')
    g.series = Series.query.filter_by(id=series_id).first_or_404()


@bp.route('/')
def index():
    return "TODO"


@bp.route('/patch/<page_index>')
def patch():
    return "TODO"


@bp.route('/mbox')
def mbox():
    return "TODO"
