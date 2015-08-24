from wtforms import fields
from wtforms import form
from wtforms import validators

from flask.ext.security import RegisterForm, current_user


class ExtendedRegisterForm(RegisterForm):
    name = fields.TextField('Full Name', [validators.Required()])


class ProfileForm(form.Form):
    old_password = fields.PasswordField('Old Password', [
        validators.Optional(),
    ])
    password = fields.PasswordField('New Password', [
        validators.Optional(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = fields.PasswordField('Repeat Password')
    submit = fields.SubmitField('Apply')

    def validate_old_password(self, field):
        user = current_user
        if user and not user.is_valid_password(self.old_password.data):
            raise validators.ValidationError('Old password is incorrect!')

    def merge_user(self, user):
        if self.password.validate():
            user.set_password(self.password.data)


class GitHubRegistrationForm(form.Form):
    password = fields.PasswordField('New Password', [
        validators.Optional(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = fields.PasswordField('Repeat Password')
    submit = fields.SubmitField('Apply')
    name = fields.TextField('Name', [validators.Required()])
    github_username = fields.TextField('GitHub username', [validators.Required()])
    email = fields.TextField('email', [validators.Required()])

    def validate_confirm(self, field):
        if not len(field.data) >= 8:
            raise validators.ValidationError('Password should be at least 8 characters long')

    def merge_user(self, user):
        if self.password.validate():
            user.set_password(self.password.data)
