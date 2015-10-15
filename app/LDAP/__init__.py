from flask import Flask
from flask.ext.login import LoginManager

app = Flask(__name__, static_url_path='')

app.config.from_object('config')

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
lm.login_message = 'Please log in to access this page.'

from app import views
