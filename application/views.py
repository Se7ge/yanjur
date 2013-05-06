# -*- encoding: utf-8 -*-
from flask import render_template, abort
from application.app import app
from admin.models import Pages
from admin.database import Session


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/page/<url>')
def show_article(url):
    page = Session().query(Pages).filter(Pages.url == url).first()
    if page:
        return render_template('article.html', article=page)
    else:
        abort(404)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404