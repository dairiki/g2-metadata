#! -*- coding: utf-8 -*-
""" Code for dumping ORM-mapped gallery data to YAML.
"""
from __future__ import absolute_import

from collections import (
    defaultdict,
    OrderedDict,
    Mapping,
    Sequence,
    )
from datetime import datetime
import re

import sqlalchemy as sa
import yaml

from . import models


class Dumper(yaml.Dumper):
    _anchor_ids = defaultdict(lambda: 1)

    def generate_anchor(self, node):
        # To aid readability, add type to anchors to our custom tags
        tag = node.tag
        if tag.startswith('!'):
            prefix = tag[1:].lower()
        else:
            prefix = 'id'
        anchor_id = self._anchor_ids[prefix]
        self._anchor_ids[prefix] = anchor_id + 1
        return "%s%03d" % (prefix, anchor_id)

    def represent_datetime(self, data):
        # Hack to get datetimes with 'T' separator, and 'Z' zone
        return self.represent_scalar(
            u'tag:yaml.org,2002:timestamp',
            data.replace(microsecond=0).isoformat() + u'Z')

    def represent_unicode(self, data):
        style = None
        if '\n' in data:
            # Translate from DOS to UNIX newline conventions
            lines = re.split('\r?\n', data)
            max_len = max(len(line) for line in lines)
            style = '>' if max_len > 65 else '|'
            data = '\n'.join(lines)
        return self.represent_scalar(u'tag:yaml.org,2002:str', data, style)

    def represent_long(self, data):
        return self.represent_scalar(u'tag:yaml.org,2002:int', unicode(data))

    omit_attrs = ('derivatives', 'children')     # FIXME

    def represent_object(self, obj):
        if hasattr(obj, '__yaml_representation__'):
            return obj.__yaml_representation__(self)
        elif isinstance(obj, OrderedDict):
            # Prevent yaml from sorting keys
            return self.represent_mapping(
                'tag:yaml.org,2002:map', obj.items(), False)
        elif isinstance(obj, Mapping):
            # handle, e.g., sa.orm.collections.CollectionAdapter
            return self.represent_mapping(
                'tag:yaml.org,2002:map', obj, False)
        elif isinstance(obj, Sequence):
            # handle, e.g., sa.orm.collections.InstrumentedList
            return self.represent_sequence(
                'tag:yaml.org,2002:seq', obj, False)
        else:
            raise RuntimeError(
                "Can not represent object {0!r}"
                " of type {0.__class__.__module__}.{0.__class__.__name__}"
                " with mro {0.__class__.__mro__!r}"
                .format(obj))


Dumper.add_representer(datetime, Dumper.represent_datetime)
Dumper.add_representer(unicode, Dumper.represent_unicode)
Dumper.add_representer(long, Dumper.represent_long)
Dumper.add_multi_representer(object, Dumper.represent_object)


class TestDumper(object):
    def dump(self, data):
        dumped = yaml.dump(data, Dumper=Dumper)
        ENDING = '\n...\n'
        assert dumped.endswith(ENDING)
        return dumped[:-len(ENDING)]

    def test_represent_datetime(self):
        dt = datetime(2011, 2, 3, 4, 5, 6, 7)
        assert self.dump(dt) == '2011-02-03T04:05:06Z'

    def test_represent_unicode(self):
        assert self.dump(u'abc') == u'abc'

    def test_represent_long(self):
        assert self.dump(42L) == u'42'


def get_gallery_metadata(session):
    """ Get all pertinent data from the db.
    """
    # Precache all the items in the gallery, so we don't have to query each one
    # individually.
    # derivatives = models.Item.derivatives.of_type(
    #    sa.orm.with_polymorphic(models.Derivative, [models.DerivativeImage],
    #                            aliased=True))
    cache_items = (             # noqa
        session.query(models.Item)
        .with_polymorphic([
            models.AlbumItem,
            models.LinkItem,
            models.MovieItem,
            models.PhotoItem,
            ])
        .options(
            sa.orm.subqueryload('parent'),
            sa.orm.subqueryload('linked_item'),
            sa.orm.subqueryload('linked_from_item'),
            sa.orm.subqueryload('subitems'),
            sa.orm.subqueryload('comments'),
            # sa.orm.subqueryload('_plugin_parameters'),
            sa.orm.subqueryload(models.AlbumItem._plugin_parameters),
            sa.orm.subqueryload(models.User._plugin_parameters),
            sa.orm.subqueryload(models.ChildEntity.parent),
            sa.orm.subqueryload('owner'),
            sa.orm.subqueryload('accessList').joinedload('userOrGroup'),
            # sa.orm.subqueryload(derivatives).joinedload('source'),
            )
        ).all()

    data = OrderedDict()
    data['groups'] = session.query(models.Group).all()
    data['users'] = session.query(models.User).all()
    data['plugin_parameters'] = models.get_global_plugin_parameters(session)

    # Find the top-level album for the gallery
    data['album'] = session.query(models.AlbumItem).filter_by(parentId=0)\
                                                   .one()
    return data


def dump_metadata(session, stream):
    data = get_gallery_metadata(session)
    yaml.dump(data, stream, Dumper,
              width=65,
              default_flow_style=False,
              explicit_start=True)
