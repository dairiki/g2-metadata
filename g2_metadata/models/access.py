# -*- coding: utf-8 -*-
"""
"""
from __future__ import absolute_import

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    text,
    )
from sqlalchemy.orm import backref, relationship

from .base import Base, metadata, g_Column, g_Table
from .util import cache_json
from .entity import Entity
from .plugin import PluginParametersMixin


class User(Entity, PluginParametersMixin):
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


t_PermissionSetMap = g_Table(
    'PermissionSetMap', metadata,
    g_Column('module', String(128), nullable=False),
    g_Column('permission', String(128), nullable=False, unique=True),
    g_Column('description', String(255)),
    g_Column('bits', Integer, nullable=False, server_default=text("'0'")),
    g_Column('flags', Integer, nullable=False, server_default=text("'0'"))
    )


class AccessMap(Base):
    accessListId = Column(Integer, primary_key=True, nullable=False,
                          index=True, server_default=text("'0'"))
    permission = Column(Integer, nullable=False, index=True,
                        server_default=text("'0'"))
    userOrGroupId = Column(ForeignKey(Entity.id),
                           primary_key=True, nullable=False,
                           index=True, server_default=text("'0'"))

    _identity = relationship(Entity, foreign_keys=[userOrGroupId])

    def __json__(self, omit=()):
        from .item import AlbumItem, LinkItem, PhotoItem  # circdep
        identity = self._identity
        if identity is None:
            assert self.userOrGroupId == 0, \
                "missing userOrGroupid %d" % self.userOrGroupId
            return None
        types = {
            User: 'user',
            Group: 'group',
            AlbumItem: 'album_item',
            PhotoItem: 'album_item',
            LinkItem: 'album_item',
            }
        identity_key = types[type(identity)]
        return {
            'permission': self.permission,
            identity_key: identity.__json__(omit=omit),
            }


class AccessSubscriberMap(Base):
    itemId = Column(ForeignKey(Entity.id), primary_key=True,
                    server_default=text("'0'"))
    accessListId = Column(ForeignKey(AccessMap.accessListId),
                          nullable=False, index=True,
                          server_default=text("'0'"))


class AccessList(list):
    # This is all just a hack to sanely cache the return values
    # from __json__, so that identical accessLists return the
    # same list (not just an identical list).
    def _keyfunc(self, omit=()):
        ids = frozenset(entry.accessListId for entry in self)
        return (ids, frozenset(omit))

    _global_cache = {}

    @cache_json(use_list=True, cache=_global_cache, keyfunc=_keyfunc)
    def __json__(self, omit=()):
        return [entry.__json__(omit) for entry in self]


AccessMap._listed = relationship(
    Entity,
    secondary=AccessSubscriberMap.__table__,
    backref=backref('accessList', collection_class=AccessList))
