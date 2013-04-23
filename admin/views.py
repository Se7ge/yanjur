# -*- coding: utf-8 -*-

import os
from flask import request, redirect, url_for
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.admin.base import expose, BaseView
from wtforms.fields import SelectField, BooleanField, FileField
from admin.database import Session
from werkzeug import secure_filename

from admin.models import Action, Person, Person_Alias, Place, Work_Categories, Work_Person, Work, Title
from admin.models import Connection_Type, Connection, Work_Time
from settings import UPLOAD_FOLDER
from parser import parse_sheet

ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])


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

    def __init__(self, session, **kwargs):
        super(Person_AliasAdmin, self).__init__(Person_Alias, session, **kwargs)


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


class Connection_TypeAdmin(ModelView):
    column_labels = dict(name=u'Название типа сотрудничества')

    def __init__(self, session, **kwargs):
        super(Connection_TypeAdmin, self).__init__(Connection_Type, session, **kwargs)


class Work_TimeAdmin(ModelView):
    column_labels = dict(name=u'Временной период')

    def __init__(self, session, **kwargs):
        super(Work_TimeAdmin, self).__init__(Work_Time, session, **kwargs)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


class UploadAdmin(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def upload_file(self):
        msg = None
        if request.method == 'POST':
            category = int(request.form['category'])
            if category:
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