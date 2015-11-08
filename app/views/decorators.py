from functools import wraps
from flask import render_template, request, url_for
from app.models import PatchState

def filterable(f):
    """Filter a query"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        d = f(*args, **kwargs)

        q = d['query']

        state = request.args.get('state', None, type=str)
        if state:
            q = q.filter_by(state=PatchState.from_string(state))

        # add more filters later
        d['query'] = q
        return d
    return wrapped


def paginable(pagename, max_per_page=50):
    """Paginate a query"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            d = f(*args, **kwargs)

            q = d['query']

            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', max_per_page, type=int)

            p = q.paginate(page, per_page, False)

            if not p.items:
                d['page'] = None
                d[pagename] = q.paginate(1, per_page, False)
            else:
                d[pagename] = p
            return d
        return wrapped
    return decorator


def render(template):
    """render a query"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            d = f(*args, **kwargs)
            def endpoint(**up):
                args = dict()
                args.update(request.args)
                args.update(up)
                return url_for(request.endpoint, **args)

            d['endpoint'] = endpoint
            return render_template(template, **d)
        return wrapped
    return decorator
