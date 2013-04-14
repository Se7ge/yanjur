# -*- coding: utf-8 -*-
from flask import Flask, request, session
from flask.ext.admin import Admin
from flask.ext.babelex import Babel
from settings import FLASK_SECRET_KEY
from admin.database import Session
from admin import views

app = Flask(__name__)
app.debug = True
app.secret_key = FLASK_SECRET_KEY
admin = Admin(app, name=u'Администрирование')

# Initialize babel
babel = Babel(app)


@babel.localeselector
def get_locale():
    override = request.args.get('lang')

    if override:
        session['lang'] = override

    return session.get('lang', 'ru')

admin.add_view(views.Person_AliasAdmin(Session, name=u'Псевдонимы авторов'))
admin.add_view(views.Work_Categories(Session, name=u'Сборники'))


@app.teardown_request
def shutdown_session(exception=None):
    Session.remove()