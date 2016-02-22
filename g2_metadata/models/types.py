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
        if value is None:
            return None
        return datetime.utcfromtimestamp(value)
