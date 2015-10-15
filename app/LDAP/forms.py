from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, validators, PasswordField
from wtforms.validators import Required, Length


class LoginForm(Form):
    username = TextField("Username", validators=[Length(min=2, max=25), Required()])
    password = PasswordField('Password', [validators.Required()])    
    # remember_me = BooleanField('remember_me', default = False)