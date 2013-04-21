# -*- coding: utf-8 -*-

from xlrd import open_workbook
from database import Session
from admin.models import Action, Connection, Connection_Type, Person, Person_Alias, Place, Title, Work, Work_Categories
from admin.models import Work_Person, Work_Time, Work_Person_Actions, Work_Person_Titles, Connection_Titles

WORK_CATEGORY = 1  # Брать из формы

WORK_COLUMNS = [dict(table=Work, column='number'),
                dict(table=Work, column='name'),
                dict(table=Work, column='location'),
                dict(table=Work, column='concordance'),
                dict(table=Work, column='colophon')]

AUTHOR_COLUMNS = [
    dict(table=Person, column='name', link_column='person_id', link_table=Work_Person, multiple=False),
    dict(table=Title, column='name', link_column='title_id', link_table=Work_Person_Titles, multiple=True),
    dict(table=Action, column='name', link_column='action_id', link_table=Work_Person_Actions, multiple=True),
    dict(table=Work_Time, column='name', link_column='time_id', link_table=Work_Person, multiple=False),
    dict(table=Place, column='name', link_column='place_id', link_table=Work_Person, multiple=False)]

CONNECTION_COLUMNS = [
    dict(table=Connection_Type, column='name', link_column='connect_type_id', link_table=Connection, multiple=False),
    dict(table=Person, column='name', link_column='person_id', link_table=Connection, multiple=False),
    dict(table=Title, column='name', link_column='title_id', link_table=Connection_Titles, multiple=True)]

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
    return session.query(_class).filter_by(**{column: value.strip()}).first()


def _add_object(_class, column, value):
    obj = object.__new__(_class)
    setattr(obj, column, value.strip())
    session.add(obj)
    session.commit()
    return obj


def _add_work(data_row):
    objects = dict()
    object_id = None
    setattr(objects[Work.__name__], 'category_id', WORK_CATEGORY)
    for i in range(len(WORK_COLUMNS)):
        if data_row[i]:
            table_name = WORK_COLUMNS[i]['table'].__name__
            if i == 0 and table_name == Work.__name__:
                work_obj = _get_work(data_row[i])
                if work_obj:
                    objects[table_name] = work_obj
            if table_name not in objects:
                objects[table_name] = object.__new__(WORK_COLUMNS[i]['table'])
            setattr(objects[table_name], WORK_COLUMNS[i]['column'], data_row[i].strip())
    if objects:
        for obj in objects.values():
            if not hasattr(obj, 'id'):
                session.add(obj)
            session.commit()
            object_id = obj.id
    return object_id


def __process_field(table, field, value):
    _object = _get_object(table, field, value)
    if not _object:
        _object = _add_object(table, field, value)
    if _object:
        return _object


def _clear_person_work(work_id):
    for work_person in session.query(Work_Person).filter(Work_Person.work_id == work_id).all():
        session.query(Work_Person_Actions).filter(Work_Person_Actions.work_person_id == work_person.id).delete()
        session.query(Work_Person_Titles).filter(Work_Person_Titles.work_person_id == work_person.id).delete()
        work_person.delete()


def _add_author(work_id, data_row):
    fields = dict()
    for i in range(len(WORK_COLUMNS), len(WORK_COLUMNS) + len(AUTHOR_COLUMNS)):
        k = i - len(WORK_COLUMNS)
        if data_row[i]:
            if AUTHOR_COLUMNS[k]['multiple'] and data_row[i]:
                values = data_row[i].split(';')
                if values:
                    fields[AUTHOR_COLUMNS[k]['link_table'].__name__][AUTHOR_COLUMNS[k]['link_column']] = list()
                    for value in values:
                        _object = __process_field(AUTHOR_COLUMNS[k]['table'], 'name', value)
                        if _object:
                            (fields[AUTHOR_COLUMNS[k]['link_table'].__name__][AUTHOR_COLUMNS[k]['link_column']]
                             .append(_object.id))
            else:
                _object = __process_field(AUTHOR_COLUMNS[k]['table'], 'name', data_row[i])
                if _object:
                    fields[AUTHOR_COLUMNS[k]['link_table'].__name__][AUTHOR_COLUMNS[k]['link_column']] = _object.id
    if fields:
        _clear_person_work(work_id)
        work_person = None
        if fields[Work_Person.__name__]:
            fields[Work_Person.__name__]['work_id'] = work_id
            work_person = Work_Person(**fields[Work_Person.__name__])
            session.add(work_person)
            session.commit()
            del fields[Work_Person.__name__]
        if work_person and fields:
            for key, value in fields.items():
                if isinstance(value, dict):
                    for k, v in value:
                        if isinstance(v, list):
                            for el_id in v:
                                _obj = object.__new__(key)
                                setattr(_obj, k, el_id)
                                setattr(_obj, 'work_person_id', work_person.id)
                                session.add(_obj)
                                session.commit()
                        else:
                            _obj = object.__new__(key)
                            setattr(_obj, k, v)
                            setattr(_obj, 'work_person_id', work_person.id)
                            session.add(_obj)
                            session.commit()


def _clear_connection(work_person_id):
    for connection in session.query(Connection).filter(Connection.work_person_id == work_person_id).all():
        session.query(Connection_Titles).filter(Connection_Titles.connection_id == connection.id).delete()
        connection.delete()


def __add_connection(work_person_id, connection):
    fields = dict()
    if connection:
        for k, v in connection:
            if not v:
                return None
            obj = __process_field(CONNECTION_COLUMNS[k]['table'], 'name', v)
            if CONNECTION_COLUMNS[k]['multiple']:
                values = v.split(';')
                if values:
                    fields[CONNECTION_COLUMNS[k]['link_table'].__name__][CONNECTION_COLUMNS[k]['link_column']] = list()
                    for value in values:
                        _object = __process_field(CONNECTION_COLUMNS[k]['table'], 'name', value)
                        if _object:
                            (fields[CONNECTION_COLUMNS[k]['link_table'].__name__][CONNECTION_COLUMNS[k]['link_column']]
                             .append(_object.id))
            else:
                fields[CONNECTION_COLUMNS[k]['link_table'].__name__][CONNECTION_COLUMNS[k]['link_column']] = obj.id
    if fields:
        _clear_connection(work_person_id)
        fields[Connection.__name__]['work_person_id'] = work_person_id
        connection = None
        if fields[Connection.__name__]:
            fields[Connection.__name__]['work_person_id'] = work_person_id
            connection = Connection(**fields[Connection.__name__])
            session.add(connection)
            session.commit()
            del fields[Connection.__name__]
        if connection and fields:
            for key, value in fields.items():
                if isinstance(value, dict):
                    for k, v in value:
                        if isinstance(v, list):
                            for el_id in v:
                                _obj = object.__new__(key)
                                setattr(_obj, k, el_id)
                                setattr(_obj, 'connection_id', connection.id)
                                session.add(_obj)
                                session.commit()
                        else:
                            _obj = object.__new__(key)
                            setattr(_obj, k, v)
                            setattr(_obj, 'connection_id', connection.id)
                            session.add(_obj)
                            session.commit()


def _add_connections(work_person_id, data_row):
    values = data_row[len(WORK_COLUMNS) + len(AUTHOR_COLUMNS):]
    for connection in [values[i:i+3] for i in range(0, len(values), 3)]:
        __add_connection(work_person_id, connection)


def add_data(sheet):
    work_id = None
    for row in range(sheet.nrows):
        if row == 0:
            continue
        if sheet.cell(row, 0).value != '':
            work_id = _add_work(sheet.row(row))
        elif work_id:
            work_person_id = _add_author(work_id, sheet.row(row))
            if work_person_id:
                _add_connections(work_person_id, sheet.row(row))


def _add_alias(data_row):
    person_id = None
    for k, v in data_row:
        if not v:
            continue
        if k == 0:
            obj = __process_field(Person, 'name', v)
            person_id = obj.id
        elif person_id:
            obj = __process_field(Person_Alias, 'name', v)
            obj.person_id = obj.id
            session.commit()


def add_aliases(sheet):
    for row in range(sheet.nrows):
        if row == 0:
            continue
        _add_alias(sheet.row(row))


def parse_sheet(file_name):
    wb = open_workbook(file_name)
    if wb:
        for s in wb.sheets():
            if s.number == 0:
                add_data(s)
            elif s.number == 1:
                add_aliases(s)

parse_sheet('index3.xlsx')