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

    @property
    def __yaml_attributes__(self):
        cls = type(self)
        if not hasattr(cls, '_yaml_attributes'):
            attrs = set(attr for attr in dir(self) if not attr.startswith('_'))
            attrs.discard('metadata')
            columns = sa.inspect(self).mapper.columns

            def order(attr):
                order = {
                    'path': -1,
                    'comments': 1,
                    'owner': 2,
                    'accessList': 3,
                    'plugin_parameters': 4,
                    'derivative_prefs': 4,
                    'subitems': 5,
                    'hilight': 6,
                    'parent': 7,
                    }.get(attr)
                if order is None:
                    # Plain column attributes before relations
                    order = 0 if attr in columns else 1
                return order, attr
            cls._yaml_attributes = sorted(attrs, key=order)
        return cls._yaml_attributes

    def __yaml_representation__(self, dumper):
        tag = '!%s' % self.__class__.__name__
        omit_attrs = getattr(dumper, 'omit_attrs', ())  # FIXME: hackish
        items = [(attr, getattr(self, attr))
                 for attr in self.__yaml_attributes__
                 if attr not in omit_attrs]
        return dumper.represent_mapping(tag, items, False)

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
