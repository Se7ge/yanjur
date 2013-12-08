# -*- coding: utf-8 -*-
from flask import Flask, request, session
from flask.ext.admin import Admin
from flask.ext.babelex import Babel
from settings import SECRET_KEY
from admin.database import Session
from admin import views

app = Flask(__name__)
app.debug = True
app.secret_key = SECRET_KEY
admin = Admin(app, name=u'Администрирование')

# Initialize babel
babel = Babel(app)


@babel.localeselector
def get_locale():
    override = request.args.get('lang')

    if override:
        session['lang'] = override

    return session.get('lang', 'ru')

admin.add_view(views.Pages_Admin(Session, name=u'Статьи'))
admin.add_view(views.Work_Admin(Session, name=u'Сочинения'))
admin.add_view(views.Person_Admin(Session, name=u'Авторы', category=u'Справочники'))
admin.add_view(views.Person_AliasAdmin(Session, name=u'Псевдонимы авторов', category=u'Синонимы'))
admin.add_view(views.Action_AliasAdmin(Session, name=u'Синонимы действий', category=u'Синонимы'))
admin.add_view(views.Title_AliasAdmin(Session, name=u'Синонимы титулов', category=u'Синонимы'))
admin.add_view(views.Place_AliasAdmin(Session, name=u'Синонимы топонимов', category=u'Синонимы'))
admin.add_view(views.ActionsAdmin(Session, name=u'Действия', category=u'Справочники'))
admin.add_view(views.PlaceAdmin(Session, name=u'Местоположения', category=u'Справочники'))
admin.add_view(views.Work_TimeAdmin(Session, name=u'Периоды времени', category=u'Справочники'))
admin.add_view(views.Work_CategoriesAdmin(Session, name=u'Сборники', category=u'Справочники'))
# admin.add_view(views.Connection_ActionAdmin(Session, name=u'Типы сотрудничества', category=u'Справочники'))
admin.add_view(views.TitlesAdmin(Session, name=u'Титулы', category=u'Справочники'))
admin.add_view(views.UploadAdmin(name=u'Загрузка данных'))
admin.add_view(views.Users_Admin(Session, name=u'Пользователи', category=u'Пользователи'))
admin.add_view(views.Roles_Admin(Session, name=u'Роли', category=u'Пользователи'))

from views_ck import ck_browse, ck_upload


@app.teardown_request
def shutdown_session(exception=None):
    Session.remove()