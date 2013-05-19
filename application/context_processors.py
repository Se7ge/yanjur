# -*- coding: utf-8 -*-

from application.app import app
from admin.models import Person, Person_Alias, Action, Title, Work_Categories, Work, Place, Work_Time
from admin.database import Session

session = Session()


@app.context_processor
def sidebar_menu():
    works = session.query(Work).order_by('number')
    persons = session.query(Person).order_by('name')
    titles = session.query(Title).order_by('name')
    actions = session.query(Action).order_by('name')
    places = session.query(Place).order_by('name')
    times = session.query(Work_Time).order_by('name')
    return dict(works=works,
                persons=persons,
                titles=titles,
                actions=actions,
                places=places,
                times=times)