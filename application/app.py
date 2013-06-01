# -*- coding: utf-8 -*-
from flask import Flask
from settings import DEBUG

app = Flask(__name__)
app.debug = DEBUG

from application.views import *


@app.teardown_request
def shutdown_session(exception=None):
    Session.remove()


if __name__ == '__main__':
    app.run()
