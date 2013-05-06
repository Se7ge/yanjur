# -*- coding: utf-8 -*-
from flask import Flask
app = Flask(__name__)

from application.views import *


if __name__ == '__main__':
    app.run()