# -*- coding: utf-8 -*-

from xlrd import open_workbook
from database import Session
from admin.models import Action, Connection, Connection_Type, Person, Person_Alias, Place, Title, Work, Work_Categories
from admin.models import Work_Person, Work_Time

WORK_CATEGORY = 1  # Брать из формы

WORK_COLUMNS = [dict(table=Work, column='number'),
                dict(table=Work, column='name'),
                dict(table=Work, column='location'),
                dict(table=Work, column='concordance'),
                dict(table=Work, column='colophon')]

AUTHOR_COLUMNS = [dict(table=Person, column='name', link_column='person_id'),
                  dict(table=Title, column='name', link_column='title_id'),
                  dict(table=Action, column='name', link_column='action_id'),
                  dict(table=Work_Time, column='name', link_column='time_id'),
                  dict(table=Place, column='name', link_column='place_id')]

CONNECTION_COLUMNS = [dict(table=Connection_Type, column='name'),
                      dict(table=Person, column='name'),
                      dict(table=Title, column='name')]

session = Session()


def _get_work(number):
    return session.query(Work).filter(Work.number == number.strip(), Work.category_id == WORK_CATEGORY).first()


def _get_author(name):
    author = session.query(Person).filter(Person.name == name.strip()).first()
    if not author:
        person_alias = session.query(Person_Alias).filter(Person_Alias.name == name.strip()).first()
        if person_alias:
            author = person_alias.person
    return author


def _get_object(_class, column, value):
    return session.query(_class).filter_by(**{column: value}).first()


def _add_object(_class, column, value):
    obj = _class(**{column: value})
    session.add(obj)
    session.commit()
    return obj


def _add_work(data_row):
    objects = dict()
    object_id = None
    setattr(objects[Work.__name__], 'category_id', WORK_CATEGORY)
    for i in xrange(len(WORK_COLUMNS)):
        if data_row[i]:
            table_name = WORK_COLUMNS[i]['table'].__name__
            if i == 0 and table_name == Work.__name__:
                work_obj = _get_work(data_row[i])
                if work_obj:
                    objects[table_name] = work_obj
            if table_name not in objects:
                objects[table_name] = WORK_COLUMNS[i]['table']
            setattr(objects[table_name], WORK_COLUMNS[i]['column'], data_row[i])
    if objects:
        for obj in objects.values():
            if not hasattr(obj, 'id'):
                session.add(obj)
            session.commit()
            object_id = obj.id
    return object_id


def _add_author(work_id, data_row):
    fields = dict()
    for i in xrange(len(WORK_COLUMNS), len(WORK_COLUMNS) + len(AUTHOR_COLUMNS)):
        k = i - len(WORK_COLUMNS)
        if data_row[i]:
            _object = _get_object(AUTHOR_COLUMNS[k]['table'], 'name', data_row[i])
            if not _object:
                _object = _add_object(AUTHOR_COLUMNS[k]['table'], 'name', data_row[i])
            if _object:
                fields[AUTHOR_COLUMNS[k]['link_column']] = _object.id
    if fields:
        # TODO: TITLE & ACTION m/b/ MANY!!!!!!!!!!!!!!
        fields['work_id'] = work_id
        session.add(Work_Person(**fields))
        session.commit()


def _add_connection(work_person_id, data_row):
    pass


def add_data(sheet):
    work_id = None
    for row in xrange(sheet.nrows):
        if row == 0:
            continue
        if sheet.cell(row, 0).value != '':
            work_id = _add_work(sheet.row(row))
        elif work_id:
            work_person_id = _add_author(work_id, sheet.row(row))
            if work_person_id:
                _add_connection(work_person_id, sheet.row(row))


def add_aliases(sheet):
    pass


def parse_sheet(file_name):
    wb = open_workbook(file_name)
    if wb:
        for s in wb.sheets():
            if s.number == 0:
                add_data(s)
            elif s.number == 1:
                # TODO: сначала alias, чтобы связывать работы?
                # TODO: делать ли alias - многие-ко-многим для Person? или как тогда указать псевдоним в качестве автора произведения?
                # если сначала привязали автора, а потом поняли, что это псевдоним, что делать?
                add_aliases(s)

parse_sheet('index3.xlsx')