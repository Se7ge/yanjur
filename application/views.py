# -*- encoding: utf-8 -*-
from flask import render_template, abort
from application.app import app
from admin.models import Pages, Work, Work_Time, Action, Title, Place, Person
from admin.database import Session
from application.context_processors import sidebar_menu


session = Session()
ENTITIES = dict(works=Work, persons=Person, titles=Title, actions=Action, places=Place, times=Work_Time)


@app.route('/')
def index():
    return render_template('base.html')


@app.route('/page/<url>/')
def show_article(url):
    page = session.query(Pages).filter(Pages.url == url).first()
    if page:
        return render_template('article.html', article=page)
    else:
        abort(404)


@app.route('/<name>/')
def entity_list(name):
    order_by = 'name'
    if name == 'works':
        order_by = 'number'
    data = session.query(ENTITIES[name]).order_by(order_by)
    return render_template('%s/entity_list.html' % name, data=data)


@app.route('/work/<int:id>.html')
def work(id):
    work = session.query(Work).get(id)
    if work:
        return render_template('entity.html', entity='work', entity_id=id, data=work)
    else:
        abort(404)


@app.route('/person/<int:id>.html')
def person(id):
    person = session.query(Person).get(id)
    if person:
        return render_template('persons/entity.html', entity='person', entity_id=id, data=person)
    else:
        abort(404)


@app.route('/title/<int:id>.html')
def title(id):
    title = session.query(Title).get(id)
    if title:
        return render_template('titles/entity.html', entity='title', entity_id=id, data=title)
    else:
        abort(404)


@app.route('/action/<int:id>.html')
def action(id):
    action = session.query(Action).get(id)
    if action:
        return render_template('actions/entity.html', entity='action', entity_id=id, data=action)
    else:
        abort(404)


@app.route('/place/<int:id>.html')
def place(id):
    place = session.query(Place).get(id)
    if place:
        return render_template('places/entity.html', entity='place', entity_id=id, data=place)
    else:
        abort(404)


@app.route('/time/<int:id>.html')
def time(id):
    time = session.query(Work_Time).get(id)
    if time:
        return render_template('times/entity.html', entity='time', entity_id=id, data=time)
    else:
        abort(404)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404