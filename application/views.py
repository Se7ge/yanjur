# -*- encoding: utf-8 -*-
from flask import render_template, abort, request, url_for, json
from application.app import app
from admin.models import Pages, Work, Work_Time, Action, Title, Place, Person, Work_Person, Work_Person_Titles
from admin.models import Work_Person_Actions, Connection, Connection_Titles
from admin.database import Session
from application.context_processors import sidebar_menu
from settings import SEARCHD_CONNECTION

from sphinxit.core.nodes import Count, OR, RawAttr
from sphinxit.core.processor import Search, Snippet


class SearchConfig(object):
    DEBUG = app.debug
    WITH_META = True
    WITH_STATUS = True
    SEARCHD_CONNECTION = SEARCHD_CONNECTION


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
        order_by = 'number+0'
    data = session.query(ENTITIES[name]).order_by(order_by)
    return render_template('%s/entity_list.html' % name, data=data)


@app.route('/search/')
def search():
    template = 'index.html'
    data = None
    if request.args.get('q'):
        search = Search(['works'], config=SearchConfig)
        search = search.match(request.args.get('q')).limit(0, 1000)
        result = search.ask()
        if result['result']:
            ids = list()
            for item in result['result']:
                ids.append(item['id'])
            if ids:
                data = session.query(Work).filter(Work.id.in_(ids)).all()

        template = 'result.html'
    return render_template('search/%s' % template, data=data)


@app.route('/work/<int:id>.html')
def work(id):
    work = session.query(Work).get(id)
    if work:
        context_links = _get_context_links(id)
        return render_template('works/entity.html',
                               entity='work',
                               entity_id=id,
                               data=work,
                               links=context_links)
    else:
        abort(404)


def _get_context_links(work_id):
    result = list()

    persons = session.query(Person).join(Work_Person).filter(Work_Person.work_id == work_id).all()
    if persons:
        for person in persons:
            if person.name:
                result.append(dict(name=person.name, url=url_for('person', id=person.id)))
            if person.aliases:
                for alias in person.aliases:
                    if alias.name:
                        result.append(dict(name=alias.name, url=url_for('person', id=person.id)))

    titles = (session.query(Title)
              .join(Work_Person_Titles)
              .join(Work_Person)
              .filter(Work_Person.work_id == work_id)
              .all())
    if titles:
        for title in titles:
            if title.name:
                result.append(dict(name=title.name, url=url_for('title', id=title.id)))

    actions = (session.query(Action)
               .join(Work_Person_Actions)
               .join(Work_Person)
               .filter(Work_Person.work_id == work_id)
               .all())
    if actions:
        for action in actions:
            if action.name:
                result.append(dict(name=action.name, url=url_for('action', id=action.id)))

    places = session.query(Place).join(Work_Person).filter(Work_Person.work_id == work_id).all()
    if places:
        for place in places:
            if place.name:
                result.append(dict(name=place.name, url=url_for('place', id=place.id)))

    times = session.query(Work_Time).join(Work_Person).filter(Work_Person.work_id == work_id).all()
    if times:
        for time in times:
            if time.name:
                result.append(dict(name=time.name, url=url_for('time', id=time.id)))

    connection_persons = (session.query(Person)
                          .join(Connection)
                          .join(Work_Person)
                          .filter(Work_Person.work_id == work_id)
                          .all())
    if connection_persons:
        for person in connection_persons:
            if person.name:
                result.append(dict(name=person.name, url=url_for('person', id=person.id)))
            if person.aliases:
                for alias in person.aliases:
                    if alias.name:
                        result.append(dict(name=person.name, url=url_for('person', id=person.id)))

    connection_titles = (session.query(Title)
                         .join(Connection_Titles)
                         .join(Connection)
                         .join(Work_Person)
                         .filter(Work_Person.work_id == work_id)
                         .all())
    if connection_titles:
        for title in connection_titles:
            if title.name:
                result.append(dict(name=title.name, url=url_for('title', id=title.id)))

    return result


@app.route('/person/<int:id>.html')
def person(id):
    person = session.query(Person).get(id)

    person_titles = list()
    query = (session.query(Title)
             .join(Work_Person_Titles)
             .join(Work_Person)
             .filter(Work_Person.person_id == id)
             .order_by(Title.name))
    for title in query.all():
        works = (session.query(Work_Person)
                 .join(Work_Person_Titles)
                 .join(Work)
                 .filter(Work_Person_Titles.title_id == title.id, Work_Person.person_id == id)
                 .order_by(Work.number)
                 .all())
        person_titles.append(dict(title=title, works=works))

    person_actions = list()
    query = (session.query(Action)
             .join(Work_Person_Actions)
             .join(Work_Person)
             .filter(Work_Person.person_id == id)
             .order_by(Action.name))
    for action in query.all():
        works = (session.query(Work_Person)
                 .join(Work_Person_Actions)
                 .join(Work)
                 .filter(Work_Person_Actions.action_id == action.id, Work_Person.person_id == id)
                 .order_by(Work.number)
                 .all())
        person_actions.append(dict(action=action, works=works))

    person_times = list()
    query = (session.query(Work_Time)
             .join(Work_Person)
             .filter(Work_Person.person_id == id)
             .order_by(Work_Time.name))
    for time in query.all():
        works = (session.query(Work_Person)
                 .join(Work)
                 .filter(Work_Person.time_id == time.id, Work_Person.person_id == id)
                 .order_by(Work.number)
                 .all())
        person_times.append(dict(time=time, works=works))

    person_places = list()
    query = (session.query(Place)
             .join(Work_Person)
             .filter(Work_Person.person_id == id)
             .order_by(Place.name))
    for place in query.all():
        works = (session.query(Work_Person)
                 .join(Work)
                 .filter(Work_Person.place_id == place.id, Work_Person.person_id == id)
                 .order_by(Work.number)
                 .all())
        person_places.append(dict(place=place, works=works))

    if person:
        return render_template('persons/entity.html',
                               entity='person',
                               entity_id=id,
                               person=person,
                               person_titles=person_titles,
                               person_actions=person_actions,
                               person_times=person_times,
                               person_places=person_places,)
    else:
        abort(404)


@app.route('/title/<int:id>.html')
def title(id):
    title = session.query(Title).get(id)
    person_titles = list()
    query = (session.query(Person)
             .join(Work_Person)
             .join(Work_Person_Titles)
             .filter(Work_Person_Titles.title_id == id)
             .order_by(Person.name))
    for person in query.all():
        works = (session.query(Work_Person)
                 .join(Work_Person_Titles)
                 .join(Work)
                 .filter(Work_Person_Titles.title_id == id, Work_Person.person_id == person.id)
                 .order_by(Work.number)
                 .all())
        person_titles.append(dict(person=person, works=works))

    if title:
        return render_template('titles/entity.html',
                               entity='title',
                               entity_id=id,
                               entity_data=title,
                               person_titles=person_titles)
    else:
        abort(404)


@app.route('/action/<int:id>.html')
def action(id):
    action = session.query(Action).get(id)
    person_actions = list()
    query = (session.query(Person)
             .join(Work_Person)
             .join(Work_Person_Actions)
             .filter(Work_Person_Actions.action_id == id)
             .order_by(Person.name))
    for person in query.all():
        works = (session.query(Work_Person)
                 .join(Work_Person_Actions)
                 .join(Work)
                 .filter(Work_Person_Actions.action_id == id, Work_Person.person_id == person.id)
                 .order_by(Work.number)
                 .all())
        person_actions.append(dict(person=person, works=works))
    if action:
        return render_template('actions/entity.html',
                               entity='action',
                               entity_id=id,
                               entity_data=action,
                               person_actions=person_actions)
    else:
        abort(404)


@app.route('/place/<int:id>.html')
def place(id):
    place = session.query(Place).get(id)
    person_places = list()
    query = (session.query(Person)
             .join(Work_Person)
             .filter(Work_Person.place_id == id)
             .order_by(Person.name))
    for person in query.all():
        works = (session.query(Work_Person)
                 .join(Work)
                 .filter(Work_Person.place_id == id, Work_Person.person_id == person.id)
                 .order_by(Work.number)
                 .all())
        person_places.append(dict(person=person, works=works))
    if place:
        return render_template('places/entity.html',
                               entity='place',
                               entity_id=id,
                               entity_data=place,
                               person_places=person_places)
    else:
        abort(404)


@app.route('/time/<int:id>.html')
def time(id):
    time = session.query(Work_Time).get(id)
    person_times = list()
    query = (session.query(Person)
             .join(Work_Person)
             .filter(Work_Person.time_id == id)
             .order_by(Person.name))
    for person in query.all():
        works = (session.query(Work_Person)
                 .join(Work)
                 .filter(Work_Person.time_id == id, Work_Person.person_id == person.id)
                 .order_by(Work.number)
                 .all())
        person_times.append(dict(person=person, works=works))
    if time:
        return render_template('times/entity.html',
                               entity='time',
                               entity_id=id,
                               entity_data=time,
                               person_times=person_times)
    else:
        abort(404)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
