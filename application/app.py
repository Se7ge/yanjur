# -*- coding: utf-8 -*-
from flask import Flask
from settings import DEBUG
from admin.database import shutdown_session, Session

app = Flask(__name__)
app.debug = DEBUG

from application.views import *


@app.teardown_request
def shutdown_session(exception=None):
    Session.close()


if __name__ == '__main__':
    app.run()
