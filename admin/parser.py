# -*- coding: utf-8 -*-

from xlrd import open_workbook
from database import Session
from admin.models import Action, Connection, Connection_Type, Person, Person_Alias, Place, Title, Work, Work_Categories
from admin.models import Work_Person

WORK_CATEGORY = 1  # Брать из формы

DATA_COLUMNS = [dict(table=Work, column='number'),
                dict(table=Work, column='name'),
                dict(table=Work, column='location'),
                dict(table=Work, column='concordance'),
                dict(table=Work, column='colophon'),
                dict(table=Work, column='name'),
                ]


def add_data(sheet):
    pass


def add_aliases(sheet):
    pass


def parse_sheet(file_name):
    wb = open_workbook(file_name)
    if wb:
        for s in wb.sheets():
            if s.number == 0:
                add_data(s)
            elif s.number == 1:
                add_aliases(s)

parse_sheet('index3.xlsx')