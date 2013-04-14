# -*- coding: utf-8 -*-

from flask import request
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.admin.base import expose, BaseView
from wtforms.fields import SelectField, BooleanField

from admin.models import Action, Person, Person_Alias, Place, Work_Categories, Work_Person, Work, Title
from admin.models import Connection_Type, Connection


class Person_AliasAdmin(ModelView):
    column_labels = dict(person=u'Автор', name=u'Псевдоним')

    def __init__(self, session, **kwargs):
        super(Person_AliasAdmin, self).__init__(Person_Alias, session, **kwargs)


class Work_CategoriesAdmin(ModelView):
    column_labels = dict(name=u'Название сборника', code=u'Код сборника(?)')

    def __init__(self, session, **kwargs):
        super(Work_CategoriesAdmin, self).__init__(Work_Categories, session, **kwargs)