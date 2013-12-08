# -*- coding: utf-8 -*-

import os
from flask import request, redirect, url_for
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.admin.base import expose, BaseView
from wtforms.fields import SelectField, BooleanField, FileField
from admin.database import Session
from werkzeug import secure_filename

from admin.models import Action, Person, Person_Alias, Place, Work_Categories, Work_Person, Work, Title, Pages
from admin.models import Title_Alias, Connection, Work_Time, Connection_Actions, Action_Alias, Place_Alias
from admin.models import Work_Person_Titles, Connection_Titles, Roles, Users
from admin.ckedit import CKTextAreaField
from settings import UPLOAD_FOLDER
from parser import parse_sheet

ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])

session = Session()


class Work_Admin(ModelView):
    column_labels = dict(number=u'№', name=u'Название', colophon=u'Колофон', category=u'Сборник')

    def __init__(self, session, **kwargs):
        super(Work_Admin, self).__init__(Work, session, **kwargs)


class Person_Admin(ModelView):
    column_labels = dict(name=u'Имя')

    def __init__(self, session, **kwargs):
        super(Person_Admin, self).__init__(Person, session, **kwargs)


class Person_AliasAdmin(ModelView):
    column_labels = dict(person=u'Автор', name=u'Псевдоним')
    form_columns = ('person', 'name')
    column_list = ('person', 'name')
    column_sortable_list = (('person', Person.name), 'name')

    def __init__(self, session, **kwargs):
        super(Person_AliasAdmin, self).__init__(Person_Alias, session, **kwargs)


class Action_AliasAdmin(ModelView):
    column_labels = dict(action=u'Действие', name=u'Синоним')
    form_columns = ('action', 'name')
    column_list = ('action', 'name')
    column_sortable_list = (('action', Action.name), 'name')

    def __init__(self, session, **kwargs):
        super(Action_AliasAdmin, self).__init__(Action_Alias, session, **kwargs)


class Place_AliasAdmin(ModelView):
    column_labels = dict(place=u'Топоним', name=u'Синоним')
    form_columns = ('place', 'name')
    column_list = ('place', 'name')

    def __init__(self, session, **kwargs):
        super(Place_AliasAdmin, self).__init__(Place_Alias, session, **kwargs)


class Title_AliasAdmin(ModelView):
    column_labels = dict(title=u'Титул', name=u'Синоним')
    form_columns = ('title', 'name')
    column_list = ('title', 'name')

    def __init__(self, session, **kwargs):
        super(Title_AliasAdmin, self).__init__(Title_Alias, session, **kwargs)


class Work_CategoriesAdmin(ModelView):
    column_labels = dict(name=u'Название сборника', code=u'Код сборника(?)')

    def __init__(self, session, **kwargs):
        super(Work_CategoriesAdmin, self).__init__(Work_Categories, session, **kwargs)


class ActionsAdmin(ModelView):
    column_labels = dict(name=u'Название действия')

    def __init__(self, session, **kwargs):
        super(ActionsAdmin, self).__init__(Action, session, **kwargs)


class TitlesAdmin(ModelView):
    column_labels = dict(name=u'Название титула')

    def __init__(self, session, **kwargs):
        super(TitlesAdmin, self).__init__(Title, session, **kwargs)


class PlaceAdmin(ModelView):
    column_labels = dict(name=u'Название места')

    def __init__(self, session, **kwargs):
        super(PlaceAdmin, self).__init__(Place, session, **kwargs)


class Connection_ActionAdmin(ModelView):
    column_labels = dict(name=u'Название типа сотрудничества')

    def __init__(self, session, **kwargs):
        super(Connection_ActionAdmin, self).__init__(Connection_Actions, session, **kwargs)


class Work_TimeAdmin(ModelView):
    column_labels = dict(name=u'Временной период')

    def __init__(self, session, **kwargs):
        super(Work_TimeAdmin, self).__init__(Work_Time, session, **kwargs)


class Pages_Admin(ModelView):
    column_labels = dict(title=u'Заголовок',
                         title_en=u'Заголовок (English)',
                         text=u'Текст статьи',
                         text_en=u'Текст статьи (English)',
                         url=u'URL-адрес страницы')
    column_list = ('title', 'url')
    form_overrides = dict(text=CKTextAreaField, text_en=CKTextAreaField)

    create_template = 'create.html'
    edit_template = 'edit.html'

    def __init__(self, session, **kwargs):
        super(Pages_Admin, self).__init__(Pages, session, **kwargs)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def _delete_aliases(aliases):
    for alias in aliases:
        session.delete(alias)
        session.commit()


def __delete_actions(actions):
    for action in actions:
        _delete_aliases(action.aliases)
        session.delete(action)
        session.commit()


def __delete_titles(titles):
    for title in titles:
        _delete_aliases(title.aliases)
        session.delete(title)
        session.commit()


def __delete_person(person):
    _delete_aliases(person.aliases)
    session.delete(person)
    session.commit()


def __delete_time(time):
    session.delete(time)
    session.commit()


def __delete_place(place):
    _delete_aliases(place.aliases)
    session.delete(place)
    session.commit()


def __delete_work(work):
    session.delete(work)
    session.commit()


def __delete_connections(connections):
    actions = list()
    persons = list()
    titles = list()
    for connection in connections:
        actions.append(connection.actions)
        persons.append(connection.person)
        titles.append(
            session.query(Title).join(Connection_Titles).filter(
                Connection_Titles.connection_id == connection.id
            ).all())
        session.delete(connection)
        session.commit()
    return actions, persons, titles


def clear_works(category_id):
    work_persons = session.query(Work_Person).filter(Work.category_id == category_id).all()
    actions = list()
    persons = list()
    times = list()
    titles = list()
    places = list()
    for work_person in work_persons:
        actions.append(work_person.actions)
        persons.append(work_person.person)
        times.append(work_person.times)
        places.append(work_person.places)
        titles.append(
            session.query(Title).join(Work_Person_Titles).filter(
                Work_Person_Titles.work_person_id == work_person.id
            ).all())

        con_actions, con_persons, con_titles = __delete_connections(work_person.connections)
        actions.extend(con_actions)
        persons.extend(con_persons)
        titles.extend(con_titles)

        session.delete(work_person)
        session.commit()

    for action in actions:
        if action:
            __delete_actions(action)

    for title in titles:
        if title:
            __delete_titles(title)

    for person in persons:
        if person:
            __delete_person(person)

    for time in times:
        if time:
            __delete_time(time)

    for place in places:
        if place:
            __delete_place(place)

    session.query(Work).filter(Work.category_id == category_id).delete()
    session.commit()


def clear_data(category_id):
    clear_works(category_id)


class UploadAdmin(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def upload_file(self):
        msg = None
        if request.method == 'POST':
            category = int(request.form['category'])
            if category:
                if request.form.get('clear_old'):
                    clear_data(category)

                _file = request.files['file']
                if _file and allowed_file(_file.filename):
                    filename = secure_filename(_file.filename)
                    _file.save(os.path.join(UPLOAD_FOLDER, filename))
                    parse_sheet(int(request.form['category']), os.path.join(UPLOAD_FOLDER, filename))
                    return self.render('upload_result.html', msg=u'Загрузка файла успешна!')
                else:
                    msg = u'Попытка загрузить файл неверного формата'
            else:
                msg = u'Не выбран сборник, к которому относится файл'
        return self.render('upload.html', categories=Session().query(Work_Categories).all(), msg=msg)


class Roles_Admin(ModelView):
    column_labels = dict(name=u'Имя', code=u'Код')
    form_columns = ('code', 'name')

    def __init__(self, session, **kwargs):
        super(Roles_Admin, self).__init__(Roles, session, **kwargs)


class Users_Admin(ModelView):
    column_labels = dict(login=u'Логин', password=u'Пароль', active=u'Активен')
    form_columns = ('login', 'password', 'active', 'roles')

    def __init__(self, session, **kwargs):
        super(Users_Admin, self).__init__(Users, session, **kwargs)
