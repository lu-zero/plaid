from wtforms import form, fields, validators
from app import db
from app.models import User


# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    email = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])
    remember_me = fields.BooleanField()
    submit = fields.SubmitField('Login')

    def validate_email(self, field):
        user = self.get_user()
        if user is None:
            raise validators.ValidationError('Invalid user')

    def validate_password(self, field):
        user = self.get_user()
        if user and user.is_valid_password(self.password.data):
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        email = self.email.data.strip()
        return db.session.query(User).filter_by(email=email).first()


class RegistrationForm(form.Form):
    email = fields.TextField(validators=[validators.required(),
                                         validators.Email()])
    password = fields.PasswordField('New Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = fields.PasswordField('Repeat Password')
    name = fields.TextField(validators=[validators.required()])
    submit = fields.SubmitField('Register')

    def validate_email(self, field):
        if db.session.query(User).filter_by(email=self.email.data).count() > 0:
            raise validators.ValidationError('E-Mail already used. Did you '
                                             'forget your password?')
