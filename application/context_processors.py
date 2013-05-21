# -*- coding: utf-8 -*-

from application.app import app
from admin.models import Person, Person_Alias, Action, Title, Work_Categories, Work, Place, Work_Time
from admin.database import Session

session = Session()


@app.context_processor
def sidebar_menu():
    works = session.query(Work).order_by('number').count()
    persons = session.query(Person).order_by('name').count()
    titles = session.query(Title).order_by('name').count()
    actions = session.query(Action).order_by('name').count()
    places = session.query(Place).order_by('name').count()
    times = session.query(Work_Time).order_by('name').count()
    return dict(works=works,
                persons=persons,
                titles=titles,
                actions=actions,
                places=places,
                times=times)