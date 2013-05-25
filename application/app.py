# -*- coding: utf-8 -*-
from flask import Flask
app = Flask(__name__)

from application.views import *


@app.teardown_request
def shutdown_session(exception=None):
    Session.remove()


if __name__ == '__main__':
    app.run()