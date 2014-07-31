import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask_oauth import OAuth
from flask.ext.mail import Mail
from config import basedir, ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'users'
oauth = OAuth()
mail = Mail(app)

facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': ('email, ')}
)

#if not app.debug and MAIL_SERVER != '':
#    import logging
#    from logging.handlers import SMTPHandler
#    credentials = None
#    if MAIL_USERNAME or MAIL_PASSWORD:
#        credentials = (MAIL_USERNAME, MAIL_PASSWORD)
#    mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT), 'no-reply@' + MAIL_SERVER, ADMINS, 'microblog failure', credentials)
#    mail_handler.setLevel(logging.ERROR)
#    app.logger.addHandler(mail_handler)

#if not app.debug and os.environ.get('HEROKU') is None:
#    import logging
#    from logging.handlers import RotatingFileHandler
#    file_handler = RotatingFileHandler('tmp/coopkot.log', 'a', 1 * 1024 * 1024, 10)
#    file_handler.setLevel(logging.INFO)
#    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
#    app.logger.addHandler(file_handler)
#    app.logger.setLevel(logging.INFO)
#    app.logger.info('coopkot startup')

#if os.environ.get('HEROKU') is not None:
#    import logging
#    stream_handler = logging.StreamHandler()
#    app.logger.addHandler(stream_handler)
#    app.logger.setLevel(logging.INFO)
#    app.logger.info('coopkot startup')

from app import views, models

