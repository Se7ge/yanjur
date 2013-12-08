# -*- encoding: utf-8 -*-
from flask import render_template, abort, request, url_for, json, current_app, redirect, session
import jinja2
from sqlalchemy import func, or_, desc
from flask.ext.principal import Identity, AnonymousIdentity, identity_changed
from application.app import app, login_manager
from application.utils import public_endpoint
from admin.models import Pages, Work, Work_Time, Action, Title, Place, Person, Work_Person, Work_Person_Titles
from admin.models import Work_Person_Actions, Connection, Connection_Titles, Connection_Actions, Title_Alias
from admin.models import Person_Alias, Action_Alias, Place_Alias, Users
from admin.database import Session
from application.context_processors import sidebar_menu
from application.forms import LoginForm
from application.user import User
from settings import SEARCHD_CONNECTION, AUTH_REQUIRED
from flask.ext.login import login_user, logout_user, login_required, current_user
from functools import wraps

from sphinxit.core.nodes import Count, OR, RawAttr
from sphinxit.core.processor import Search, Snippet


class SearchConfig(object):
    DEBUG = app.debug
    WITH_META = True
    WITH_STATUS = True
    SEARCHD_CONNECTION = SEARCHD_CONNECTION


db_session = Session()
ENTITIES = dict(works=Work, persons=Person, titles=Title, actions=Action, places=Place, times=Work_Time)


login_manager.login_view = 'login'


def exclude_endpoint(endpoint, exclude):
    for item in exclude:
        if item in endpoint:
            return True
    return False


def my_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if AUTH_REQUIRED:
            if current_app.login_manager._login_disabled:
                return func(*args, **kwargs)
            elif not current_user.is_authenticated():
                return current_app.login_manager.unauthorized()
            return func(*args, **kwargs)
    return decorated_view


@app.before_request
def check_valid_login():
    login_valid = current_user.is_authenticated()

    exclude_list = ['static']

    if (request.endpoint and
            not exclude_endpoint(request.endpoint, exclude_list) and
            not login_valid and
            not getattr(app.view_functions[request.endpoint], 'is_public', False)):
        return redirect(url_for('login', next=url_for(request.endpoint)))


@app.route('/login/', methods=['GET', 'POST'])
@public_endpoint
def login():
    # login form that uses Flask-WTF
    form = LoginForm()
    errors = list()

    # Validate form input
    if form.validate_on_submit():
        # Retrieve the user from the hypothetical datastore
        user = db_session.query(Users).filter(Users.login == form.login.data.strip()).first()
        if user:
            check_user = User(user.login)
            # Compare passwords (use password hashing production)
            if check_user.check_password(form.password.data.strip(), user.password):
                # Keep the user info in the session using Flask-Login
                login_user(user)

                # Tell Flask-Principal the identity changed
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

                return redirect(request.args.get('next') or url_for('index'))
            else:
                errors.append(u'Access denied')
        else:
            errors.append(u'Access denied <b>%s</b>' % form.login.data.strip())

    return render_template('user/login.html', form=form, errors=errors)


@app.route('/logout/')
def logout():
    # Remove the user information from the session
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())

    return redirect(request.args.get('next') or '/')


@app.route('/')
@my_login_required
def index():
    page = db_session.query(Pages).filter(Pages.url == 'index').first()
    if page:
        return render_template('index.html', article=page)
    else:
        abort(404)


@app.route('/page/<url>/')
@my_login_required
def show_article(url):
    page = db_session.query(Pages).filter(Pages.url == url).first()
    if page:
        return render_template('article.html', article=page)
    else:
        abort(404)


@app.route('/places/')
@my_login_required
def places_list():
    data = db_session.query(Place).join(Work_Person).join(Work).order_by(Place.name).all()
    for key, item in enumerate(data):
        exists_works = []
        works = []
        for kk, work_person in enumerate(item.works):
            if work_person.work_id not in exists_works:
                works.append(work_person)
            exists_works.append(work_person.work_id)
        item.works = works
    return render_template('places/entity_list.html', data=data)


@app.route('/times/')
@my_login_required
def times_list():
    data = db_session.query(Work_Time).join(Work_Person).join(Work).order_by(Work_Time.name).all()
    for item in data:
        exists_works = []
        works = []
        for kk, work_person in enumerate(item.works):
            if work_person.work_id not in exists_works:
                works.append(work_person)
            exists_works.append(work_person.work_id)
        item.works = works
    return render_template('times/entity_list.html', data=data)


@app.route('/<name>/')
@my_login_required
def entity_list(name):
    order_by = 'name'
    if name == 'works':
        order_by = '''
        SUBSTRING_INDEX(number, ' ', 1),
        LENGTH(SUBSTRING_INDEX(number, '(', 1)),
        SUBSTRING_INDEX(number, '(', 1)'''
    data = db_session.query(ENTITIES[name]).order_by(order_by).all()
    return render_template('%s/entity_list.html' % name, data=data)


@app.route('/search/')
@my_login_required
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
                data = db_session.query(Work).filter(Work.id.in_(ids)).all()

        template = 'result.html'
    return render_template('search/%s' % template, data=data)


@app.route('/work/<int:id>.html')
@my_login_required
def work(id):
    title_aliases = db_session.query(Title_Alias).all()
    work = db_session.query(Work).get(id)
    if work:
        context_links = _get_context_links(id)

        concordances = work.concordance.split(';')
        if not isinstance(concordances, list):
            concordances = list(concordances)
        concordance_works = db_session.query(Work).filter(Work.number.in_(map(lambda x: x.strip(), concordances))).all()

        return render_template('works/entity.html',
                               entity='work',
                               entity_id=id,
                               data=work,
                               concordance=concordance_works,
                               links=context_links)
    else:
        abort(404)


def _get_context_links_only_by_work(work_id):
    result = list()

    persons_query = db_session.query(Person).join(Work_Person).filter(Work_Person.work_id == work_id)
    connection_persons = (db_session.query(Person)
                          .join(Connection)
                          .join(Work_Person)
                          .filter(Work_Person.work_id == work_id))

    persons = persons_query.union(connection_persons).group_by(Person.id).order_by(desc(func.length(Person.name))).all()
    if persons:
        _exists = []
        for person in persons:
            if person.name and person.name not in _exists:
                _exists.append(person.name)
                result.append(dict(name=person.name, url=url_for('person', id=person.id)))
                # result.update({person.name: url_for('person', id=person.id)})
            if person.aliases:
                for alias in person.aliases:
                    if alias.name and alias.name not in _exists:
                        _exists.append(alias.name)
                        result.append(dict(name=jinja2.escape(alias.name), url=url_for('person', id=person.id)))
                        # result.update({alias.name: url_for('person', id=person.id)})

    titles_query = (db_session.query(Title)
                    .join(Work_Person_Titles)
                    .join(Work_Person)
                    .filter(Work_Person.work_id == work_id))

    connection_titles = (db_session.query(Title)
                         .join(Connection_Titles)
                         .join(Connection)
                         .join(Work_Person)
                         .filter(Work_Person.work_id == work_id))
    titles = titles_query.union(connection_titles).group_by(Title.id).order_by(desc(func.length(Title.name))).all()
    if titles:
        _exists = []
        for title in titles:
            if title.name and title.name not in _exists:
                _exists.append(title.name)
                # result.update({title.name: url_for('title', id=title.id)})
                result.append(dict(name=jinja2.escape(title.name), url=url_for('title', id=title.id)))
            if title.aliases:
                for alias in title.aliases:
                    if alias.name and alias.name not in _exists:
                        _exists.append(alias.name)
                        # result.update({alias.name: url_for('title', id=title.id)})
                        result.append(dict(name=jinja2.escape(alias.name), url=url_for('title', id=title.id)))

    actions_query = (db_session.query(Action)
                     .join(Work_Person_Actions)
                     .join(Work_Person)
                     .filter(Work_Person.work_id == work_id))
    connection_actions = (db_session.query(Action)
                          .join(Connection_Actions)
                          .join(Connection)
                          .join(Work_Person)
                          .filter(Work_Person.work_id == work_id))
    actions = actions_query.union(connection_actions).group_by(Action.id).order_by(desc(func.length(Action.name))).all()
    if actions:
        _exists = []
        for action in actions:
            if action.name and action.name not in _exists:
                _exists.append(action.name)
                # result.update({action.name: url_for('action', id=action.id)})
                result.append(dict(name=jinja2.escape(action.name), url=url_for('action', id=action.id)))
            if action.aliases:
                for alias in action.aliases:
                    if alias.name and alias.name not in _exists:
                        _exists.append(alias.name)
                        # result.update({alias.name: url_for('action', id=action.id)})
                        result.append(dict(name=jinja2.escape(alias.name), url=url_for('action', id=action.id)))

    places = (db_session.query(Place)
              .join(Work_Person)
              .filter(Work_Person.work_id == work_id)
              .order_by(desc(func.length(Place.name)))
              .all())
    if places:
        _exists = []
        for place in places:
            if place.name and place.name not in _exists:
                _exists.append(place.name)
                # result.update({place.name: url_for('place', id=place.id)})
                result.append(dict(name=jinja2.escape(place.name), url=url_for('place', id=place.id)))
            if place.aliases:
                for alias in place.aliases:
                    if alias.name and alias.name not in _exists:
                        _exists.append(alias.name)
                        # result.update({alias.name: url_for('place', id=place.id)})
                        result.append(dict(name=jinja2.escape(alias.name), url=url_for('place', id=place.id)))

    times = (db_session.query(Work_Time)
             .join(Work_Person)
             .filter(Work_Person.work_id == work_id)
             .order_by(desc(func.length(Work_Time.name)))
             .all())
    if times:
        _exists = []
        for time in times:
            if time.name and time.name not in _exists:
                _exists.append(time.name)
                # result.update({time.name: url_for('time', id=time.id)})
                result.append(dict(name=jinja2.escape(time.name), url=url_for('time', id=time.id)))

    return result


def _get_context_links(work_id):
    result = list()

    persons = db_session.query(Person).order_by(desc(func.length(Person.name))).all()
    if persons:
        _exists = []
        for person in persons:
            if person.name and person.name not in _exists:
                _exists.append(person.name)
                result.append(dict(name=jinja2.escape(person.name), url=url_for('person', id=person.id)))
                # result.update({person.name: url_for('person', id=person.id)})

    person_aliases = db_session.query(Person_Alias).order_by(desc(func.length(Person_Alias.name))).all()
    if person_aliases:
        for person_alias in person_aliases:
            if person_alias.name and person_alias.name not in _exists:
                _exists.append(person_alias.name)
                result.append(
                    dict(name=jinja2.escape(person_alias.name), url=url_for('person', id=person_alias.person_id)))

    titles = db_session.query(Title).order_by(desc(func.length(Title.name))).all()
    if titles:
        _exists = []
        for title in titles:
            if title.name and title.name not in _exists:
                _exists.append(title.name)
                # result.update({title.name: url_for('title', id=title.id)})
                result.append(dict(name=jinja2.escape(title.name), url=url_for('title', id=title.id)))

    title_aliases = db_session.query(Title_Alias).order_by(desc(func.length(Title_Alias.name))).all()
    if title_aliases:
        for title_alias in title_aliases:
            if title_alias.name and title_alias.name not in _exists:
                _exists.append(title_alias.name)
                result.append(dict(name=jinja2.escape(title_alias.name), url=url_for('title', id=title_alias.title_id)))

    actions = db_session.query(Action).order_by(desc(func.length(Action.name))).all()
    if actions:
        _exists = []
        for action in actions:
            if action.name and action.name not in _exists:
                _exists.append(action.name)
                # result.update({action.name: url_for('action', id=action.id)})
                result.append(dict(name=jinja2.escape(action.name), url=url_for('action', id=action.id)))

    action_aliases = db_session.query(Action_Alias).order_by(desc(func.length(Action_Alias.name))).all()
    if action_aliases:
        for action_alias in action_aliases:
            if action_alias.name and action_alias.name not in _exists:
                _exists.append(action_alias.name)
                result.append(
                    dict(name=jinja2.escape(action_alias.name), url=url_for('action', id=action_alias.action_id)))

    places = db_session.query(Place).order_by(desc(func.length(Place.name))).all()
    if places:
        _exists = []
        for place in places:
            if place.name and place.name not in _exists:
                _exists.append(place.name)
                result.append(dict(name=jinja2.escape(place.name), url=url_for('place', id=place.id)))

    place_aliases = db_session.query(Place_Alias).order_by(desc(func.length(Place_Alias.name))).all()
    if place_aliases:
        for place_alias in place_aliases:
            if place_alias.name and place_alias.name not in _exists:
                _exists.append(place_alias.name)
                result.append(dict(name=jinja2.escape(place_alias.name), url=url_for('place', id=place_alias.place_id)))

    times = db_session.query(Work_Time).order_by(desc(func.length(Work_Time.name))).all()
    if times:
        _exists = []
        for time in times:
            if time.name and time.name not in _exists:
                _exists.append(time.name)
                result.append(dict(name=jinja2.escape(time.name), url=url_for('time', id=time.id)))

    return result


@app.route('/person/<int:id>.html')
@my_login_required
def person(id):
    current_person = db_session.query(Person).get(id)

    person_titles = list()
    query = (db_session.query(Title)
             .join(Work_Person_Titles)
             .join(Work_Person)
             .filter(Work_Person.person_id == id))
    connection_query = (db_session.query(Title)
                        .join(Connection_Titles)
                        .join(Connection)
                        .filter(Connection.person_id == id))
    for title in query.union(connection_query).group_by(Title.id).order_by(Title.name).all():
        work_query = (db_session.query(Work_Person)
                      .join(Work_Person_Titles)
                      .join(Work)
                      .filter(Work_Person_Titles.title_id == title.id, Work_Person.person_id == id))
        connection_work_query = (db_session.query(Work_Person)
                                 .join(Connection)
                                 .join(Connection_Titles)
                                 .filter(Connection_Titles.title_id == title.id, Connection.person_id == id))
        # works = (db_session.query(Work_Person)
        #          .join(Work_Person_Titles)
        #          .join(Work)
        #          .filter(Work_Person_Titles.title_id == title.id, Work_Person.person_id == id)
        #          .order_by(Work.number)
        #          .all())
        works = work_query.union(connection_work_query).join(Work).group_by(Work_Person.id).order_by(Work.number).all()
        person_titles.append(dict(title=title, works=works))

    person_actions = list()
    query = (db_session.query(Action)
             .join(Work_Person_Actions)
             .join(Work_Person)
             .filter(Work_Person.person_id == id)
             .order_by(Action.name))
    for action in query.all():
        works = (db_session.query(Work_Person)
                 .join(Work_Person_Actions)
                 .join(Work)
                 .filter(Work_Person_Actions.action_id == action.id, Work_Person.person_id == id)
                 .order_by(Work.number)
                 .all())
        person_actions.append(dict(action=action, works=works))

    person_times = list()
    query = (db_session.query(Work_Time)
             .join(Work_Person)
             .filter(Work_Person.person_id == id)
             .order_by(Work_Time.name))
    for time in query.all():
        works = (db_session.query(Work_Person)
                 .join(Work)
                 .filter(Work_Person.time_id == time.id, Work_Person.person_id == id)
                 .order_by(Work.number)
                 .all())
        person_times.append(dict(time=time, works=works))

    person_places = list()
    query = (db_session.query(Place)
             .join(Work_Person)
             .filter(Work_Person.person_id == id)
             .order_by(Place.name))
    for place in query.all():
        works = (db_session.query(Work_Person)
                 .join(Work)
                 .filter(Work_Person.place_id == place.id, Work_Person.person_id == id)
                 .order_by(Work.number)
                 .all())
        person_places.append(dict(place=place, works=works))

    connections = (db_session.query(Connection)
                   .join(Work_Person)
                   .filter(Work_Person.person_id == id)
                   .all())

    backward_connections = (db_session.query(Connection).filter(Connection.person_id == id).all())

    connect_data = dict()
    for item in connections:
        if item.person.id not in connect_data:
            connect_data[item.person.id] = dict()
        action_ids = list()
        for action in item.actions:
            if action.id not in connect_data[item.person.id]:
                connect_data[item.person.id][action.id] = dict(person=item.person,
                                                               action=action,
                                                               works=list())
            connect_data[item.person.id][action.id]['works'].append(item.work_person.work)
    for item in backward_connections:
        person = item.work_person.person
        if person.id not in connect_data:
            connect_data[person.id] = dict()
        action_ids = list()
        for action in item.actions:
            action_ids.append(str(action.id))
            if action.id not in connect_data[person.id]:
                connect_data[person.id][action.id] = dict(person=person,
                                                          action=action,
                                                          works=list())
            connect_data[person.id][action.id]['works'].append(item.work_person.work)

    if current_person:
        return render_template('persons/entity.html',
                               entity='person',
                               entity_id=id,
                               person=current_person,
                               person_titles=person_titles,
                               person_actions=person_actions,
                               person_times=person_times,
                               person_places=person_places,
                               connect_data=connect_data)
    else:
        abort(404)


@app.route('/title/<int:id>.html')
@my_login_required
def title(id):
    title = db_session.query(Title).get(id)
    person_titles = list()
    query = (db_session.query(Person)
             .join(Work_Person)
             .join(Work_Person_Titles)
             .filter(Work_Person_Titles.title_id == id))
    connection_query = (db_session.query(Person)
                        .join(Connection)
                        .join(Connection_Titles)
                        .filter(Connection_Titles.title_id == id))
    for person in query.union(connection_query).group_by(Person.id).order_by(Person.name).all():
        work_query = (db_session.query(Work_Person)
                      .join(Work_Person_Titles)
                      .filter(Work_Person_Titles.title_id == id, Work_Person.person_id == person.id))
        work_connection_query = (db_session.query(Work_Person)
                                 .join(Connection)
                                 .join(Connection_Titles)
                                 .filter(Connection_Titles.title_id == id, Connection.person_id == person.id))
        works = work_query.union(work_connection_query).join(Work).order_by(Work.number).all()
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
@my_login_required
def action(id):
    action = db_session.query(Action).get(id)
    person_actions = list()
    query = (db_session.query(Person)
             .join(Work_Person)
             .join(Work_Person_Actions)
             .filter(Work_Person_Actions.action_id == id))
    connection_query = (db_session.query(Person)
                        .join(Connection)
                        .join(Connection_Actions)
                        .filter(Connection_Actions.action_id == id))
    backward_connection_query = (db_session.query(Person)
                                 .join(Work_Person)
                                 .join(Connection)
                                 .join(Connection_Actions)
                                 .filter(Connection_Actions.action_id == id))
    persons = (query.union(connection_query).union(backward_connection_query)
               .group_by(Person.id)
               .order_by(Person.name)
               .all())
    for person in persons:
        work_query = (db_session.query(Work_Person)
                      .join(Work_Person_Actions)
                      .filter(Work_Person_Actions.action_id == id, Work_Person.person_id == person.id))
        work_connection_query = (db_session.query(Work_Person)
                                 .join(Connection)
                                 .join(Connection_Actions)
                                 .filter(Connection_Actions.action_id == id,
                                         or_(Connection.person_id == person.id,
                                             Work_Person.person_id == person.id)))
        works = work_query.union(work_connection_query).join(Work).order_by(Work.number).all()
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
@my_login_required
def place(id):
    place = db_session.query(Place).get(id)
    person_places = list()
    query = (db_session.query(Person)
             .join(Work_Person)
             .filter(Work_Person.place_id == id)
             .order_by(Person.name))
    for person in query.all():
        works = (db_session.query(Work_Person)
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
@my_login_required
def time(id):
    time = db_session.query(Work_Time).get(id)
    person_times = list()
    query = (db_session.query(Person)
             .join(Work_Person)
             .filter(Work_Person.time_id == id)
             .order_by(Person.name))
    for person in query.all():
        works = (db_session.query(Work_Person)
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


#########################################

@login_manager.user_loader
def load_user(user_id):
    # Return an instance of the User model
    return db_session.query(Users).get(user_id)