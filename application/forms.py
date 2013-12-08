# -*- coding: utf-8 -*-
from wtforms import TextField, BooleanField, PasswordField
from flask_wtf import Form


class LoginForm(Form):
    login = TextField(u'Login')
    password = PasswordField(u'Password')