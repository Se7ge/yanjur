# -*- coding: utf-8 -*-
from flask import Flask, g, request, session
from flask.ext.babelex import Babel
from flask.ext.principal import Principal
import settings
from admin.database import shutdown_session, Session

app = Flask(__name__)
app.config.from_object(settings)
babel = Babel(app)


@babel.localeselector
def get_locale():
    override = request.args.get('lang')

    if override:
        session['lang'] = override
    return session.get('lang', request.accept_languages.best_match(['ru_RU', 'en_EN']))

from utils import login_manager
Principal(app)
login_manager.init_app(app)


from application.views import *


@app.teardown_request
def shutdown_session(exception=None):
    Session.close()


if __name__ == '__main__':
    app.run()
