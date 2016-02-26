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

    # NB: this seems not always to be a User or Group
    userOrGroup = relationship(Entity, foreign_keys=[userOrGroupId])


class AccessSubscriberMap(Base):
    itemId = Column(ForeignKey(Entity.id), primary_key=True,
                    server_default=text("'0'"))
    accessListId = Column(ForeignKey(AccessMap.accessListId),
                          nullable=False, index=True,
                          server_default=text("'0'"))


class AccessList(list):
    # This is all just a hack to sanely cache the return values
    # from __yaml_representation__, so that identical accessLists return the
    # same list (not just an identical list).
    _global_cache = {}

    def __yaml_representation__(self, dumper):
        if len(self) == 0:
            return dumper.represent_data([])  # don't alias empty lists
        cache = self._global_cache
        accessListId = self[0].accessListId
        assert all(entry.accessListId == accessListId for entry in self)
        node = cache.get(accessListId)
        if node is None:
            node = dumper.represent_sequence(u'tag:yaml.org,2002:seq', self)
            cache[accessListId] = node
        return node


AccessMap._listed = relationship(
    Entity,
    secondary=AccessSubscriberMap.__table__,
    backref=backref('accessList', collection_class=AccessList))
