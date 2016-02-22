# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sqlalchemy as sa
from sqlalchemy.ext.declarative import (
    declared_attr,
    declarative_base,
    )

TABLE_PREFIX = 'g2_'
COLUMN_PREFIX = 'g_'


class Base(object):
    @declared_attr
    def __tablename__(cls):
        return TABLE_PREFIX + cls.__name__

Base = declarative_base(cls=Base)
metadata = Base.metadata


@sa.event.listens_for(Base, 'instrument_class', propagate=True)
def _instrument_class(mapper, cls):
    """ Prefix all non-explicit column names with ``'g_``
    """
    for attr, column in cls.__dict__.items():
        if isinstance(column, sa.Column):
            if column.name == attr:
                column.name = COLUMN_PREFIX + attr


def g_Column(name, *args, **kw):
    """ Produce a column with prefixed column name.
    """
    kw.setdefault('key', name)
    g_name = COLUMN_PREFIX + name
    return sa.Column(g_name, *args, **kw)


def g_Table(name, *args, **kw):
    """ Produce a column with prefixed table name.
    """
    name = TABLE_PREFIX + name
    return sa.Table(name, *args, **kw)
