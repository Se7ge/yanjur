# -*- coding: utf-8 -*-

from xlrd import open_workbook
from database import Session
from admin.models import Action, Connection, Connection_Type, Person, Person_Alias, Place, Title, Work, Work_Categories
from admin.models import Work_Person, Work_Time, Work_Person_Actions, Work_Person_Titles, Connection_Titles
from admin.models import Title_Alias, Action_Alias, Place_Alias, Connection_Actions

# WORK_CATEGORY = 1  # Брать из формы

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
    dict(table=Action, column='name', link_column='action_id', link_table=Connection_Actions, multiple=True),
    dict(table=Person, column='name', link_column='person_id', link_table=Connection, multiple=False),
    dict(table=Title, column='name', link_column='title_id', link_table=Connection_Titles, multiple=True)]

ALIAS_MODELS = {Person.__name__: Person_Alias,
                Title.__name__: Title_Alias,
                Place.__name__: Place_Alias,
                Action.__name__: Action_Alias}

session = Session()


def _get_work(category, number):
    return session.query(Work).filter(Work.number == number.strip(), Work.category_id == category).first()


def _get_author(name):
    author = session.query(Person).filter(Person.name == name.strip()).first()
    if not author:
        person_alias = session.query(Person_Alias).filter(Person_Alias.name == name.strip()).first()
        if person_alias:
            author = person_alias.person
    return author


def _get_object(_class, column, value):
    value = value.rstrip('-')
    obj = session.query(_class).filter_by(**{column: value.strip()}).first()
    if not obj and _class.__name__ in ALIAS_MODELS:
        alias_obj = session.query(ALIAS_MODELS.get(_class.__name__)).filter_by(**{column: value.strip()}).first()
        obj = getattr(alias_obj, _class.__name__, None)
    return obj


def _add_object(_class, column, value):
    value = value.rstrip('-')
    obj = _class()
    setattr(obj, column, ' '.join(value.split()).strip())
    session.add(obj)
    session.commit()
    return obj


def _add_work(category, data_row):
    objects = dict()
    object_id = None
    for i in range(len(WORK_COLUMNS)):
        value = ' '.join(data_row[i].value.split()).strip()
        if value:
            table_name = WORK_COLUMNS[i]['table'].__name__
            if i == 0 and table_name == Work.__name__:
                work_obj = _get_work(category, data_row[i].value.strip())
                if not work_obj:
                    work_obj = _get_work(category, value)
                if work_obj:
                    objects[table_name] = work_obj
            if table_name not in objects:
                objects[table_name] = WORK_COLUMNS[i]['table']()
            setattr(objects[table_name], WORK_COLUMNS[i]['column'], value)
    setattr(objects[Work.__name__], 'category_id', category)
    if objects:
        for obj in objects.values():
            if not getattr(obj, 'id', None):
                session.add(obj)
            object_id = obj.id
    session.commit()
    return object_id


def __process_field(table, field, value):
    value = ' '.join(value.split())
    value = value.strip()
    if not value:
        return None
    _object = _get_object(table, field, value)
    if not _object:
        _object = _add_object(table, field, value)
    if _object:
        return _object


def _clear_person_work(work_id):
    # Чистим для того, чтобы данные были консистентными, т.к. если Action и Title сохранились, а автор изменился,
    # то будет ссылка на удалённый Work_Person
    for work_person in session.query(Work_Person).filter(Work_Person.work_id == work_id).all():
        _clear_connection(work_person.id)
        session.query(Work_Person_Actions).filter(Work_Person_Actions.work_person_id == work_person.id).delete()
        session.query(Work_Person_Titles).filter(Work_Person_Titles.work_person_id == work_person.id).delete()
        session.delete(work_person)
        session.commit()


def _add_author(work_id, data_row):
    if data_row[len(WORK_COLUMNS)].value == 'Name':
        return None
    fields = dict()
    for i in range(len(WORK_COLUMNS), len(WORK_COLUMNS) + len(AUTHOR_COLUMNS)):
        k = i - len(WORK_COLUMNS)
        if data_row[i].value:
            if not AUTHOR_COLUMNS[k]['link_table'].__name__ in fields:
                fields[AUTHOR_COLUMNS[k]['link_table'].__name__] = dict()
            if AUTHOR_COLUMNS[k]['multiple']:
                values = data_row[i].value.split(';')
                if values:
                    fields[AUTHOR_COLUMNS[k]['link_table'].__name__][AUTHOR_COLUMNS[k]['link_column']] = list()
                    for value in values:
                        _object = __process_field(AUTHOR_COLUMNS[k]['table'], 'name', value.strip())
                        if _object:
                            (fields[AUTHOR_COLUMNS[k]['link_table'].__name__][AUTHOR_COLUMNS[k]['link_column']]
                             .append(_object.id))
            else:
                _object = __process_field(AUTHOR_COLUMNS[k]['table'], 'name', data_row[i].value.strip())
                if _object:
                    fields[AUTHOR_COLUMNS[k]['link_table'].__name__][AUTHOR_COLUMNS[k]['link_column']] = _object.id
    if fields:
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
                    for k, v in value.items():
                        if isinstance(v, list):
                            for el_id in v:
                                _obj = globals()[key]()
                                setattr(_obj, k, el_id)
                                setattr(_obj, 'work_person_id', work_person.id)
                                session.add(_obj)
                                session.commit()
                        else:
                            _obj = globals()[key]()
                            setattr(_obj, k, v)
                            setattr(_obj, 'work_person_id', work_person.id)
                            session.add(_obj)
                            session.commit()
        if work_person:
            return work_person.id


def _clear_connection(work_person_id):
    for connection in session.query(Connection).filter(Connection.work_person_id == work_person_id).all():
        session.query(Connection_Titles).filter(Connection_Titles.connection_id == connection.id).delete()
        session.delete(connection)
        session.commit()


def __add_connection(work_person_id, connection):
    fields = dict()
    if connection:
        for k, v in enumerate(connection):
            if k == 0 and not v.value:
                return None
            if not CONNECTION_COLUMNS[k]['link_table'].__name__ in fields:
                fields[CONNECTION_COLUMNS[k]['link_table'].__name__] = dict()
            if CONNECTION_COLUMNS[k]['multiple']:
                values = v.value.split(';')
                if values:
                    fields[CONNECTION_COLUMNS[k]['link_table'].__name__][CONNECTION_COLUMNS[k]['link_column']] = list()
                    for value in values:
                        _object = __process_field(CONNECTION_COLUMNS[k]['table'], 'name', value)
                        if _object:
                            (fields[CONNECTION_COLUMNS[k]['link_table'].__name__][CONNECTION_COLUMNS[k]['link_column']]
                             .append(_object.id))
            else:
                obj = __process_field(CONNECTION_COLUMNS[k]['table'], 'name', v.value)
                fields[CONNECTION_COLUMNS[k]['link_table'].__name__][CONNECTION_COLUMNS[k]['link_column']] = obj.id
    if fields:
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
                    for k, v in value.items():
                        if isinstance(v, list):
                            for el_id in v:
                                _obj = globals()[key]()
                                setattr(_obj, k, el_id)
                                setattr(_obj, 'connection_id', connection.id)
                                session.add(_obj)
                                session.commit()
                        else:
                            _obj = globals()[key]()
                            setattr(_obj, k, v)
                            setattr(_obj, 'connection_id', connection.id)
                            session.add(_obj)
                            session.commit()


def _add_connections(work_person_id, data_row):
    values = data_row[len(WORK_COLUMNS) + len(AUTHOR_COLUMNS):]
    for connection in [values[i:i+3] for i in range(0, len(values), 3)]:
        __add_connection(work_person_id, connection)


def add_data(category, sheet):
    work_id = None
    work_person_id = None
    for row in range(sheet.nrows):
        if row == 0:
            continue
        if sheet.cell(row, 0).value.strip() != '':
            work_id = _add_work(category, sheet.row(row))
            _clear_person_work(work_id)
        if work_id:
            work_person_id = _add_author(work_id, sheet.row(row))
            if work_person_id:
                _add_connections(work_person_id, sheet.row(row))


def _add_alias(model, alias_model, fk_field, data_row):
    object_id = None
    for k, v in enumerate(data_row):
        v.value = v.value.strip()
        if not v or not v.value:
            continue
        if k == 0:
            obj = __process_field(model, 'name', v.value)
            object_id = obj.id
        elif object_id and v.value:
            values = v.value.split(';')
            for value in values:
                obj = __process_field(alias_model, 'name', value)
                if obj:
                    setattr(obj, fk_field, object_id)
                    session.commit()


def add_aliases(model, alias_model, fk_field, sheet):
    for row in range(sheet.nrows):
        if row == 0:
            continue
        _add_alias(model, alias_model, fk_field, sheet.row(row))


def parse_sheet(category, file_name):
    wb = open_workbook(file_name)
    if wb:
        for s in wb.sheets():
            if s.number == 0:
                add_data(category, s)
            elif s.number == 1:
                add_aliases(Person, Person_Alias, 'person_id', s)
            elif s.number == 2:
                add_aliases(Title, Title_Alias, 'title_id', s)
            elif s.number == 3:
                add_aliases(Place, Place_Alias, 'place_id', s)
            elif s.number == 4:
                add_aliases(Action, Action_Alias, 'action_id', s)

# parse_sheet('index3.xlsx')