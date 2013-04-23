# -*- coding: utf-8 -*-
DB_HOST = 'localhost'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = ''
DB_NAME = 'soap'
UPLOAD_FOLDER = '/path/to/the/uploads'

FLASK_SECRET_KEY = ''

from settings_local import *

DB_CONNECT_STRING = 'mysql://%s:%s@%s:%s/%s?charset=utf8' % (DB_USER , DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)