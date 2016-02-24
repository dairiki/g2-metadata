# -*- coding: utf-8 -*-
from __future__ import absolute_import

from calendar import timegm
from datetime import datetime

import sqlalchemy as sa


class Timestamp(sa.TypeDecorator):
    """A datetime.datetime column.

    These are stored as unix timestamps in the database.  On the
    python side they are naive datetime objects representing time in
    UTC.

    """
    impl = sa.Integer

    def process_bind_param(self, value, dialect):
        if isinstance(value, datetime):
            return timegm(value.utctimetuple())
        return value

    def process_result_value(self, value, dialect):
        if value is None or value == -1:
            return None
        return datetime.utcfromtimestamp(value)


class MangledBase(object):
    """ Gallery seems to HTML-escape just &quot; and &amp; in various strings.

    """
    MANGLED = (
        ('"', '&quot;'),
        ('<', '&lt;'),
        ('>', '&gt;'),
        ('&', '&amp;'),
        )

    def process_bind_param(self, value, dialect):
        if value:
            for orig, repl in self.MANGLED:
                value = value.replace(orig, repl)
        return value

    def process_result_value(self, value, dialect):
        if value:
            for orig, repl in self.MANGLED:
                value = value.replace(repl, orig)
        return value


class MangledString(MangledBase, sa.TypeDecorator):
    impl = sa.String


class MangledText(MangledBase, sa.TypeDecorator):
    impl = sa.String
