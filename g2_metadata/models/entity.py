# -*- coding: utf-8 -*-
""" The "Entity" heirarchy.
"""
from __future__ import absolute_import

import os

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    inspect,
    text,
    )
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy


from .base import Base
from .util import cache_json
from .types import Timestamp


class EntityMixin(object):
    pass                        # FIXME


class Entity(Base):
    entityType = Column(String(32), nullable=False)
    __mapper_args__ = {
        'polymorphic_on': entityType,
        'polymorphic_identity': 'GalleryEntity',
        }

    id = Column(Integer, primary_key=True, server_default=text("'0'"))
    creationTimestamp = Column(Timestamp, nullable=False, index=True,
                               server_default=text("'0'"))
    isLinkable = Column(Integer, nullable=False, index=True,
                        server_default=text("'0'"))
    linkId = Column(ForeignKey(id), index=True)
    modificationTimestamp = Column(Timestamp, nullable=False, index=True,
                                   server_default=text("'0'"))
    serialNumber = Column(Integer, nullable=False, index=True,
                          server_default=text("'0'"))
    onLoadHandlers = Column(String(128))

    linked_entity = relationship('Entity', remote_side=[id],
                                 lazy='subquery',
                                 backref='linked_from')

    link_path = association_proxy('linked_entity', 'path')

    _extra_json_attrs = [
        'link_path',
        'accessList',           # backref from .access.AccessMap._identity
        ]

    def __repr__(self):
        return "<%s[%d]>" % (self.__class__.__name__, self.id)

    @cache_json()
    def __json__(self, omit=()):
        column_attrs = inspect(self).mapper.columns.keys()
        data = dict((attr, getattr(self, attr))
                    for attr in column_attrs
                    if not attr.startswith('_') and attr not in omit)

        def to_json(obj):
            if hasattr(obj, '__json__'):
                return obj.__json__(omit)
            elif not isinstance(obj, dict) and hasattr(obj, '__iter__'):
                return list(map(to_json, obj))
            return obj

        for attr in self._extra_json_attrs:
            if attr not in omit:
                data[attr] = to_json(getattr(self, attr))

        return data


class ChildEntity(Entity):
    id = Column(ForeignKey(Entity.id), primary_key=True,
                server_default=text("'0'"))
    __mapper_args__ = {
        'polymorphic_identity': 'GalleryChildEntity',
        'inherit_condition': Entity.id == id,
        }

    parentId = Column(ForeignKey(Entity.id), nullable=False, index=True,
                      server_default=text("'0'"))

    parent = relationship(Entity, primaryjoin=parentId == Entity.id,
                          backref='children')


class FileSystemEntity(ChildEntity):
    id = Column(ForeignKey(ChildEntity.id), primary_key=True,
                server_default=text("'0'"))
    pathComponent = Column(String(128), index=True)

    @property
    def path(self):
        parent = self.parent
        if isinstance(parent, FileSystemEntity):
            assert self.pathComponent
            return os.path.join(parent.path, self.pathComponent)
        else:
            assert self.pathComponent is None
            return ''

    _extra_json_attrs = ChildEntity._extra_json_attrs + [
        'path',
        ]


class Comment(ChildEntity):
    __mapper_args__ = {'polymorphic_identity': 'GalleryComment'}

    id = Column(ForeignKey(ChildEntity.id), primary_key=True,
                server_default=text("'0'"))
    commenterId = Column(Integer, nullable=False, server_default=text("'0'"))
    host = Column(String(128), nullable=False)
    subject = Column(String(128))
    comment = Column(Text)
    date = Column(Timestamp, nullable=False, index=True,
                  server_default=text("'0'"))
    author = Column(String(128))
    publishStatus = Column(Integer, nullable=False, server_default=text("'0'"))


class ThumbnailImage(FileSystemEntity):
    __mapper_args__ = {'polymorphic_identity': 'ThumbnailImage'}

    id = Column(Integer, ForeignKey(FileSystemEntity.id), primary_key=True)
    mimeType = Column(String(128))
    size = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    itemMimeTypes = Column(String(128))
