# -*- coding: utf-8 -*-
from werkzeug.security import generate_password_hash, check_password_hash


class User(object):

    def __init__(self, login, password=None):
        self.pw_hash = None
        self.login = login
        if password:
            self.set_password(password)

    def set_password(self, password):
        #self.pw_hash = generate_password_hash(password)
        self.pw_hash = password

    def check_password(self, password, pw_hash):
        #return check_password_hash(pw_hash, password)
        return pw_hash==password