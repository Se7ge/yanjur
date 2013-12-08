# -*- coding: utf-8 -*-

from application.app import app
from admin.models import Person, Person_Alias, Action, Title, Work_Categories, Work, Place, Work_Time
from admin.database import Session
from datetime import datetime

session = Session()


@app.context_processor
def sidebar_menu():
    works = session.query(Work).count()
    persons = session.query(Person).count()
    titles = session.query(Title).count()
    actions = session.query(Action).count()
    places = session.query(Place).count()
    times = session.query(Work_Time).count()
    return dict(works=works,
                persons=persons,
                titles=titles,
                actions=actions,
                places=places,
                times=times,
                copy_year=datetime.now().strftime('%Y'))