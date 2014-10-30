# -*- coding: utf8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

FACEBOOK_APP_ID = '251477738393481'
FACEBOOK_APP_SECRET = '723ce8fda1034eaa465489362cf52b31'
    
if os.environ.get('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db') + '?check_same_thread=False'
    #SQLALCHEMY_DATABASE_URI = "postgresql://postgres@localhost/coopkot"
else:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_RECORD_QUERIES = True

# slow database query threshold (in seconds)
DATABASE_QUERY_TIMEOUT = 0.5

# email server
MAIL_SERVER = 'smtp.gmail.com' # your mailserver
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'janpecinovsky'
MAIL_PASSWORD = 'G1snrfpfilAE'

# administrator list
ADMINS = ['janpecinovsky+admin@gmail.com']

ADMIN_NAMES = ['Jan Pecinovsky']
# pagination
POSTS_PER_PAGE = 50
MAX_SEARCH_RESULTS = 50
