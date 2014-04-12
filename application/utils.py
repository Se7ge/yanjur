# -*- coding: utf-8 -*-
import re
from flask import g, current_app
from flask.ext.principal import identity_loaded, Principal, Permission, RoleNeed, UserNeed
from flask.ext.login import LoginManager, current_user
from application.app import app
from admin.models import Users, Roles
from admin.database import Session

session = Session()


def public_endpoint(function):
    function.is_public = True
    return function


with app.app_context():
    permissions = dict()
    login_manager = LoginManager()
    try:
        roles = session.query(Roles).all()
    except Exception, e:
        print e
        permissions['admin'] = Permission(RoleNeed('admin'))
    else:
        if roles:
            for role in roles:
                permissions[role.code] = Permission(RoleNeed(role.code))
        else:
            permissions['admin'] = Permission(RoleNeed('admin'))

admin_permission = permissions.get('admin')
user_permission = permissions.get('user')


SYNONYM_SYMBOLS = {'a': ["a\\'", 'a\\\\"'],
                   'e': ["e\\'", 'e\\\\"'],
                   'i': ["i\\'", 'i\\\\"'],
                   'u': ['o', "o\\'", 'o\\\\"', u'ö', "u\\'", 'u\\\\"', u"ü\\'"],
                   'g': ["k\\'", 'k\\\\"', 'k*', "g\\'", 'g\\\\"', 'g*', u'γ'],
                   'ng': ['n*'],
                   'j': ["c\\'", 'c\\\\"', 'c*', "j\\'", 'j\\\\"', 'j*', 'z', "z\\'", 'z\\\\"', 'z*'],
                   'n': ["n\\'", 'n\\\\"', 'n*'],
                   'd': ['t', "t\\'", 't', 't*', "d\\'", 'd\\\\"', 'd*', 'dh'],
                   's': ["s\\'", 's\\\\"', 's*', u'š'],
                   'b': ['p', "p\\'", 'p\\\\"', 'p*', 'f', 'bh'],
                   'm': ["m\\'"],
                   'y': ["y\\'"],
                   'q': ["q\\'"]}


def __query_synonyms(queries):
    result = queries
    query = queries[0]
    key = None
    for k, v in SYNONYM_SYMBOLS.items():
        #if key and key != k:
        #    queries = list(result)
        #for query in queries:
        if k in query:
            if k in ['g', 'n'] and 'ng' in query:
                continue
            for char in v:
                if char not in query:
                    result.append(query.replace(k, char))
        key = k
    return result


def make_search_synonyms(query):
    queries = list()
    query = query.replace("'", "\\'").replace('"', '\\\\"')
    queries.append(query)
    queries.extend(__query_synonyms(queries))
    return queries