from flask import url_for, redirect, render_template, request, flash
from app import app, db, login_manager
from app.models import *
from app.forms  import *

from wtforms import form, fields, validators

from flask.ext import admin, login
from flask.ext.admin.contrib import sqla
from flask.ext.admin.contrib.sqla.form import InlineModelConverter, get_form
from flask.ext.admin import helpers

# Initialize flask-login
# def init_login():
#     login_manager = login.LoginManager()
#     login_manager.setup_app(app)

#     # Create user loader function
#     @login_manager.user_loader
#     def load_user(user_id):
#         return db.session.query(User).get(user_id)

class Accessible(object):
    def is_accessible(self):
        return login.current_user.is_authenticated()

# Create customized model view class
class ModelView(Accessible, sqla.ModelView):
    pass

class M2MInlineModelConverter(InlineModelConverter):
    def contribute(self, model, form_class, inline_model):
        mapper = model._sa_class_manager.mapper
        info = self.get_info(inline_model)

        directions = ['ONETOMANY', 'MANYTOMANY', 'MANYTOONE']

        # Find property from target model to current model
        target_mapper = info.model._sa_class_manager.mapper

        reverse_prop = None

        for prop in target_mapper.iterate_properties:
            if hasattr(prop, 'direction') and prop.direction.name in directions:
                if issubclass(model, prop.mapper.class_):
                    reverse_prop = prop
                    break
        else:
            raise Exception('Cannot find reverse relation for model %s' % info.model)

        # Find forward property
        forward_prop = None

        for prop in mapper.iterate_properties:
            if hasattr(prop, 'direction') and prop.direction.name in directions:
                if prop.mapper.class_ == target_mapper.class_:
                    forward_prop = prop
                    break
        else:
            raise Exception('Cannot find forward relation for model %s' % info.model)

        # Remove reverse property from the list
        ignore = [reverse_prop.key]

        if info.form_excluded_columns:
            exclude = ignore + list(info.form_excluded_columns)
        else:
            exclude = ignore

        # Create converter
        converter = self.model_converter(self.session, info)

        # Create form
        child_form = info.get_form()

        if child_form is None:
            child_form = get_form(info.model,
                                  converter,
                                  only=info.form_columns,
                                  exclude=exclude,
                                  field_args=info.form_args,
                                  hidden_pk=True)

        # Post-process form
        child_form = info.postprocess_form(child_form)

        kwargs = dict()

        label = self.get_label(info, forward_prop.key)
        if label:
            kwargs['label'] = label

        # Contribute field
        setattr(form_class,
                forward_prop.key,
                self.inline_field_list_type(child_form,
                                            self.session,
                                            info.model,
                                            reverse_prop.key,
                                            info,
                                            **kwargs))

        return form_class

class CustomerModelView(ModelView):
#    inline_models = (Customer, )
    inline_model_form_converter = M2MInlineModelConverter

class InvoiceModelView(ModelView):
#    inline_models = (InvoiceItem, )
    inline_model_form_converter = M2MInlineModelConverter

# Create customized index view class
class AdminIndexView(Accessible, admin.AdminIndexView):
    pass

@app.route('/')
@app.route('/index')
def index():
    print("CurrentUserForIndex "+str(login.current_user))
    return render_template('index.html', 
        title="Homepage",user=login.current_user)


@app.route('/login', methods=('GET', 'POST'))
def login_view():
    form = LoginForm(request.form)
    if helpers.validate_form_on_submit(form):
        user = form.get_user()
        login.login_user(user,remember=form.remember_me)        
        return redirect(request.args.get("next") or url_for("index"))

    return render_template('login.html', 
        title="Login",user=login.current_user,
        form=form)


@app.route('/register/', methods=('GET', 'POST'))
def register_view():
    form = RegistrationForm(request.form)
    if helpers.validate_form_on_submit(form):
        user = User()

        form.populate_obj(user)

        db.session.add(user)
        db.session.commit()

        login.login_user(user)
        return redirect(url_for('index'))

    return render_template('login.html', form=form)


@app.route('/logout/')
def logout_view():
    login.logout_user()
    return redirect(url_for('index'))


@login_manager.user_loader
def load_user(userid):
    return User.get_by_id(userid)


#init_login()

admin = admin.Admin(app, 'Auth', index_view=AdminIndexView())
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Project, db.session))

# setup()
