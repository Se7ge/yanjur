# -*- coding: utf-8 -*-
from flask import Flask, g
from flask.ext.babelex import Babel
from settings import DEBUG
from admin.database import shutdown_session, Session

app = Flask(__name__)
app.debug = DEBUG
babel = Babel(app)


@babel.localeselector
def get_locale():
    # # if a user is logged in, use the locale from the user settings
    # user = getattr(g, 'user', None)
    # if user is not None:
    #     return user.locale
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    return request.accept_languages.best_match(['ru_RU', 'en_EN'])

from application.views import *


@app.teardown_request
def shutdown_session(exception=None):
    Session.close()


if __name__ == '__main__':
    app.run()
