# -*- coding: utf-8 -*-
from flask import Flask
from settings import DEBUG

app = Flask(__name__)
app.debug = DEBUG

from application.views import *


if __name__ == '__main__':
    app.run()