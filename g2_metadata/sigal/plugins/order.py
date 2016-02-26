# -*- coding: utf-8 -*-
""" Plugin to sort albums and media the way they were ordered in gallery2.

"""
from __future__ import absolute_import

from functools import total_ordering
from itertools import chain, repeat
import locale
import logging
import os
import random

from sigal import signals
from six import text_type

log = logging.getLogger(__name__)


@total_ordering
class backwards(object):
    """A proxy which reverses the order of comparison operations.

    """
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "{0.__class__.__name__}({0.value!r})".format(self)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if isinstance(other, backwards):
            return self.value == other.value
        else:
            return self.value == other

    def __lt__(self, other):
        if isinstance(other, backwards):
            return self.value > other.value  # Backwards!
        else:
            return self.value > other


def test_backwards():
    assert backwards(1) > backwards(2)
    assert backwards('foo') == backwards('foo')
    assert backwards(1) > 2
    assert 1 > backwards(2)
    assert 1 < 2


@total_ordering
class locale_str(text_type):
    """A string which compares according to LC_COLLATE.
    """
    def __lt__(self, other):
        return locale.strcoll(self, other) < 0

    def __eq__(self, other):
        return locale.strcoll(self, other) == 0


class _keybase(object):
    def __init__(self, *args):
        self.args = args

    def __repr__(self):
        return '{0.__class__.__name__}{0.args!r}'.format(self)


def is_album(item):
    # duck-type check for albums
    return hasattr(item, 'medias')


def by_description(item):
    return locale_str(item.description)


def by_path_component(item):
    return locale_str(os.path.basename(item.src_path))


def by_random(item):
    return random.random()


class by_meta(_keybase):
    def __call__(self, item):
        name = self.args[0]
        type_ = self.args[1] if len(self.args) > 1 else text_type
        value = item.meta.get(name, [None])[0]
        if value is not None:
            try:
                return type_(value)
            except ValueError:
                log.warning("Missing meta[%s] for sorting %s", name, item)
        return type_()


class reversekey(_keybase):
    def __call__(self, item):
        keyfunc, = self.args
        return backwards(keyfunc(item))


class ascending(_keybase):
    def __call__(self, desc):
        keyfunc, = self.args
        return keyfunc


class descending(_keybase):
    def __call__(self, desc):
        keyfunc, = self.args
        return reversekey(keyfunc)


class reversable(_keybase):
    def __call__(self, desc):
        keyfunc, = self.args
        return reversekey(keyfunc) if desc else keyfunc


class compoundkey(_keybase):
    def __call__(self, item):
        return tuple(keyfunc(item) for keyfunc in self.args)


ORDER_KEYS = {
    'orderWeight': ascending(by_meta('order-weight', int)),
    'title': reversable(by_meta('title', locale_str)),
    'summary': reversable(by_meta('summary', locale_str)),
    'keywords': reversable(by_meta('keywords', locale_str)),
    'originationTimestamp': reversable(by_meta('date')),
    'creationTimestamp': reversable(by_meta('created')),
    'modificationTimestamp': reversable(by_meta('updated')),
    'viewCount': reversable(by_meta('view-count', int)),
    # XXX: a little hokey, since item.description is HTML,
    # while in gallery it is bbcode.
    'description': reversable(by_description),
    'pathComponent': reversable(by_path_component),
    'random': ascending(by_random),

    # "pre-orders":
    'albumsFirst': descending(is_album),
    'viewedFirst': descending(by_meta('view-count', int)),
    # 'NewItems' not implemented,
    }


def sortkey(album):
    meta = album.meta
    if 'order-by' not in meta:
        return None             # No sort specified
    orders = meta.get('order-by', ['orderWeight'])[0].split('|')
    directions = meta.get('order-direction', [''])[0].split('|')
    directions = chain(directions, repeat(directions[-1]))
    keyfuncs = []
    for order, direction in zip(orders, directions):
        order = order.strip()
        keymaker = ORDER_KEYS.get(order)
        if keymaker is None:
            log.warning("Unknown sortOrder key %r for %s", order, album)
        keyfuncs.append(keymaker(desc=direction == 'desc'))

    return compoundkey(*keyfuncs)


def resort_subdirs(album):
    key = sortkey(album)
    if key:
        gallery = album.gallery
        root_path = album.path if album.path != '.' else ''

        def subalbum(subdir):
            return gallery.albums[os.path.join(root_path, subdir)]

        album.subdirs.sort(key=lambda subdir: key(subalbum(subdir)))
    add_items_attribute(album)


def resort_medias(album):
    key = sortkey(album)
    if key:
        album.medias.sort(key=key)
    add_items_attribute(album)


def add_items_attribute(album):
    """Add a new album.items attribute which contains both albums and medias
    co-mingled and ordered as specified by the sort options.

    This may be used in templates if it is desired to co-mingle albums
    and photos as gallery2 did.

    """
    album.items = album.albums + album.medias
    key = sortkey(album)
    if key:
        album.items.sort(key=key)


def register(settings):
    signals.albums_sorted.connect(resort_subdirs)
    signals.medias_sorted.connect(resort_medias)
