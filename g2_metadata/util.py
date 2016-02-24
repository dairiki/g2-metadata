# -*- coding: utf-8 -*-
"""
"""
from __future__ import absolute_import

from collections import deque
from six import binary_type


def text_(s, encoding='latin-1', errors='strict'):
    """ If ``s`` is an instance of ``binary_type``, return
    ``s.decode(encoding, errors)``, otherwise return ``s``"""
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    return s


def walk_items(item):
    items = deque([item])
    while items:
        item = items.popleft()
        items.extend(item.subitems)
        yield item
