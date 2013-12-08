# -*- coding: utf-8 -*-
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