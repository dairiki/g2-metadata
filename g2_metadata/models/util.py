# -*- coding: utf-8 -*-
"""
"""
from __future__ import absolute_import

from functools import wraps


def default_json_cache_keyfunc(self, omit=()):
    return (frozenset(omit),)


def cache_json(use_list=False, cache=None,
               keyfunc=default_json_cache_keyfunc):
    def decorate(method):
        @wraps(method)
        def wrapper(self, *args, **kw):
            key = keyfunc(self, *args, **kw)
            if cache is not None:
                cache_ = cache
            else:
                if not hasattr(self, '_json_cache'):
                    self._json_cache = {}
                cache_ = self._json_cache
            if key in cache_:
                return cache_[key]
            # Be careful to create cache entry first incase of recursive
            # jsonification
            if use_list:
                data = []
                update_data = data.extend
            else:
                data = {}
                update_data = data.update
            cache_[key] = data
            update_data(method(self, *args, **kw))
            return data
        return wrapper
    return decorate
