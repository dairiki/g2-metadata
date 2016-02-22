# -*- coding: utf-8 -*-
""" The "Entity" heirarchy.
"""
from __future__ import absolute_import

from itertools import groupby
from operator import attrgetter
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
from sqlalchemy.orm import object_session, relationship
from sqlalchemy.ext.associationproxy import association_proxy


from .base import Base, metadata, g_Column, g_Table
from .types import Timestamp

__all__ = (
    'Entity',
    'ChildEntity',
    'Comment',
    'ThumbnailImage',
    'Item',
    'AlbumItem',
    'PhotoItem',
    'MovieItem',
    'LinkItem',
    'AnimationItem',
    'DataItem',
    'UnknownItem',
    'Derivative',
    'DerivativeImage',
    'User',
    'Group',
    )


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

    _plugin_parameters = relationship(
        'PluginParameterMap',
        order_by=('[PluginParameterMap.pluginType,'
                  ' PluginParameterMap.pluginId]'))

    @property
    def plugin_parameters(self):
        # Note: Only Albums and Users seem to have plugin_parameters
        # so only add to _extra_json_attrs on those subclasses.
        from .plugin import plugin_parameters_to_dict  # circular dep
        return plugin_parameters_to_dict(self._plugin_parameters)

    _extra_json_attrs = ['link_path']

    def __repr__(self):
        return "<%s[%d]>" % (self.__class__.__name__, self.id)

    def __json__(self, omit=()):
        omit = frozenset(omit)
        if not hasattr(self, '_json_cache'):
            self._json_cache = {}
        args = (omit,)
        if args in self._json_cache:
            return self._json_cache[args]

        column_attrs = inspect(self).mapper.columns.keys()
        data = dict((attr, getattr(self, attr))
                    for attr in column_attrs
                    if not attr.startswith('_') and attr not in omit)

        self._json_cache[args] = data

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


t_Item = g_Table(
    'Item', metadata,
    g_Column('id', ForeignKey(FileSystemEntity.id),
             primary_key=True,
             server_default=text("'0'")),
    g_Column('canContainChildren', Integer, nullable=False,
             server_default=text("'0'")),
    g_Column('description', Text),
    g_Column('keywords', String(255), index=True),
    g_Column('ownerId', Integer, nullable=False, index=True,
             server_default=text("'0'")),
    g_Column('summary', String(255), index=True),
    g_Column('title', String(128), index=True),
    g_Column('viewedSinceTimestamp', Timestamp, nullable=False,
             server_default=text("'0'")),
    g_Column('originationTimestamp', Timestamp, nullable=False,
             server_default=text("'0'")),
    g_Column('renderer', String(128)),
    )

t_ItemAttributesMap = g_Table(
    'ItemAttributesMap', metadata,
    g_Column('itemId', ForeignKey(t_Item.c.id), primary_key=True,
             server_default=text("'0'"),
             key='_ItemAttributesMap_itemId'),
    g_Column('viewCount', Integer),
    g_Column('orderWeight', Integer),
    g_Column('parentSequence', String(255), nullable=False, index=True),
    )

t_ItemHiddenMap = g_Table(
    'ItemHiddenMap', metadata,
    g_Column('itemId', ForeignKey(t_Item.c.id), primary_key=True,
             key='_ItemHiddenMap_itemId'),
    )


class Item(FileSystemEntity):
    __table__ = t_Item.outerjoin(t_ItemAttributesMap)\
                      .outerjoin(t_ItemHiddenMap)

    @property
    def is_hidden(self):
        return self._ItemHiddenMap_itemId is not None

    subitems = relationship(
        'Item',
        primaryjoin='Item.id == remote(foreign(Item.parentId))',
        order_by='Item.orderWeight')

    comments = relationship(
        'Comment',
        primaryjoin='Item.id == remote(foreign(Comment.parentId))',
        order_by='Comment.date')

    derivatives = relationship(
        'Derivative',
        primaryjoin='Item.id == remote(foreign(Derivative.parentId))',
        order_by='Derivative.derivativeOrder')

    _extra_json_attrs = FileSystemEntity._extra_json_attrs + [
        'is_hidden',
        'subitems',
        'comments',
        'derivatives',
        ]


class AlbumItem(Item):
    __mapper_args__ = {'polymorphic_identity': 'GalleryAlbumItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))
    theme = Column(String(32))
    orderBy = Column(String(128))
    orderDirection = Column(String(32))

    @property
    def hilight(self):
        if self.derivatives:
            thumbnail, = self.derivatives
            hilight = thumbnail.source
            while isinstance(hilight, Derivative):
                hilight = hilight.source
            assert isinstance(hilight, Item)
            return hilight

    _extra_json_attrs = Item._extra_json_attrs + [
        'hilight',
        'plugin_parameters',
        ]


class PhotoItem(Item):
    __mapper_args__ = {'polymorphic_identity': 'GalleryPhotoItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))
    width = Column(Integer)
    height = Column(Integer)


class MovieItem(Item):
    __mapper_args__ = {'polymorphic_identity': 'GalleryMovieItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))
    width = Column(Integer)
    height = Column(Integer)
    duration = Column(Integer)


class LinkItem(Item):
    __mapper_args__ = {'polymorphic_identity': 'GalleryLinkItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))
    link = Column(Text, nullable=False)


class AnimationItem(Item):
    __mapper_args__ = {'polymorphic_identity': 'GalleryAnimationItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))
    width = Column(Integer)
    height = Column(Integer)


class DataItem(Item):
    __mapper_args__ = {'polymorphic_identity': 'GalleryDataItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))
    mimeType = Column(String(128))
    size = Column(Integer)


class UnknownItem(Item):
    __mapper_args__ = {'polymorphic_identity': 'GalleryUnknownItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))


class Derivative(ChildEntity):
    id = Column(ForeignKey(ChildEntity.id), primary_key=True,
                server_default=text("'0'"))
    __mapper_args__ = {'inherit_condition': ChildEntity.id == id}

    derivativeSourceId = Column(ForeignKey(Entity.id),
                                nullable=False, index=True,
                                server_default=text("'0'"))
    derivativeOperations = Column(String(255))
    derivativeOrder = Column(Integer, nullable=False, index=True,
                             server_default=text("'0'"))
    derivativeSize = Column(Integer)
    derivativeType = Column(Integer, nullable=False, index=True,
                            server_default=text("'0'"))
    mimeType = Column(String(128), nullable=False)
    postFilterOperations = Column(String(255))
    isBroken = Column(Integer)

    source = relationship(Entity, foreign_keys=[derivativeSourceId])

    _extra_json_attrs = ChildEntity._extra_json_attrs + [
        'source',
        ]


class DerivativeImage(Derivative):
    __mapper_args__ = {'polymorphic_identity': 'GalleryDerivativeImage'}

    id = Column(ForeignKey(Derivative.id),
                primary_key=True, server_default=text("'0'"))
    width = Column(Integer)
    height = Column(Integer)


t_DerivativePrefsMap = g_Table(
    'DerivativePrefsMap', metadata,
    g_Column('itemId', Integer, index=True),
    g_Column('order', Integer),
    g_Column('derivativeType', Integer),
    g_Column('derivativeOperations', String(255)),
    )

def _get_derivative_prefs(item):
    session = object_session(item)
    c = t_DerivativePrefsMap.c
    q = (session.query(t_DerivativePrefsMap)
         .filter_by(itemId=item.id)
         .order_by(c.derivativeType, c.order))
    return dict(
        (dtype, [pref.derivativeOperations for pref in prefs])
        for dtype, prefs in groupby(q, attrgetter('derivativeType')))

# Only AlbumItems appear to have derivative prefs
AlbumItem.derivative_prefs = property(_get_derivative_prefs)
AlbumItem._extra_json_attrs += ['derivative_prefs']


class User(Entity):
    __mapper_args__ = {'polymorphic_identity': 'GalleryUser'}

    id = Column(ForeignKey(Entity.id), primary_key=True,
                server_default=text("'0'"))
    userName = Column(String(32), nullable=False, unique=True)
    fullName = Column(String(128))
    hashedPassword = Column(String(128))
    email = Column(String(255))
    language = Column(String(128))
    locked = Column(Integer, server_default=text("'0'"))

    _extra_json_attrs = Entity._extra_json_attrs + [
        'plugin_parameters',
        ]


class Group(Entity):
    __mapper_args__ = {'polymorphic_identity': 'GalleryGroup'}

    id = Column(ForeignKey(Entity.id), primary_key=True,
                server_default=text("'0'"))
    groupType = Column(Integer, nullable=False, server_default=text("'0'"))
    groupName = Column(String(128), unique=True)


t_UserGroupMap = g_Table(
    'UserGroupMap', metadata,
    g_Column('userId', ForeignKey(User.id), nullable=False, index=True,
             server_default=text("'0'")),
    g_Column('groupId', ForeignKey(Group.id), nullable=False, index=True,
             server_default=text("'0'")),
    )

Group.users = relationship(User, secondary=t_UserGroupMap, backref='groups')
