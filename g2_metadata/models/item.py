# -*- coding: utf-8 -*-
""" Items

These represent actual nodes in the gallery: albums, photos, etc...

"""
from __future__ import absolute_import

from itertools import groupby
from operator import attrgetter

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
    )
from sqlalchemy.orm import object_session, relationship

from .base import metadata, g_Column, g_Table
from .entity import FileSystemEntity
from .access import User
from .derivative import (
    Derivative,
    t_DerivativePrefsMap,
    )
from .plugin import PluginParametersMixin
from .types import Timestamp


t_Item = g_Table(
    'Item', metadata,
    g_Column('id', ForeignKey(FileSystemEntity.id),
             primary_key=True,
             server_default=text("'0'")),
    g_Column('canContainChildren', Integer, nullable=False,
             server_default=text("'0'")),
    g_Column('description', Text),
    g_Column('keywords', String(255), index=True),
    g_Column('ownerId', ForeignKey(User.id), nullable=False, index=True,
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

    owner = relationship(
        'User', foreign_keys='[Item.ownerId]',
        )

    linked_item = relationship('Item',
                               primaryjoin='foreign(Entity.linkId) == remote(Item.id)',
                               lazy='subquery',
                               backref='linked_from_item')


class AlbumItem(Item, PluginParametersMixin):
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

    # Only AlbumItems appear to have derivative prefs
    @property
    def derivative_prefs(self):
        session = object_session(self)
        c = t_DerivativePrefsMap.c
        q = session.query(t_DerivativePrefsMap).filter_by(itemId=self.id)
        q = q.order_by(c.derivativeType, c.order)
        return dict(
            (dtype, [pref.derivativeOperations for pref in prefs])
            for dtype, prefs in groupby(q, attrgetter('derivativeType')))


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
