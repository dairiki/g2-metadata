# -*- coding: utf-8 -*-
""" A loader for our YAML.

This loads what were the SQLAlchemy-mapped instances into plain
old (non-ORM-mapped) classes.

"""
from __future__ import absolute_import

import yaml

from . import meta


class MetaLoader(yaml.Loader):
    def construct_class(self, class_name, node):
        cls = getattr(meta, class_name)
        assert isinstance(cls, type)
        return self.construct_yaml_object(node, cls)

MetaLoader.add_multi_constructor('!', MetaLoader.construct_class)


def load(stream):
    return yaml.load(stream, MetaLoader)
