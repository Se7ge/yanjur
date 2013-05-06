# -*- coding: utf-8 -*-
from flask.ext import wtf


# Define wtforms widget and field
class CKTextAreaWidget(wtf.TextArea):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class_', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(wtf.TextAreaField):
    widget = CKTextAreaWidget()