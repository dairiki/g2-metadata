# -*- coding: utf-8 -*-
""" These are tables reflected from the g2 schema which I am ignoring.
"""
from __future__ import absolute_import

from sqlalchemy import (
    Column,
    Index,
    Integer,
    String,
    Text,
    text,
    )

from .base import Base, metadata, g_Column, g_Table


class CacheMap(Base):
    key = Column(String(32), primary_key=True, nullable=False)
    value = Column(String)
    userId = Column(Integer, primary_key=True, nullable=False,
                    server_default=text("'0'"))
    itemId = Column(Integer, primary_key=True, nullable=False, index=True,
                    server_default=text("'0'"))
    # type is always 'page'
    type = Column(String(32), primary_key=True, nullable=False)
    timestamp = Column(Integer, nullable=False, server_default=text("'0'"))
    isEmpty = Column(Integer)
    __table_args__ = (
        Index('g2_CacheMap_21979', userId, timestamp, isEmpty),
        )


# This table is empty
t_CustomFieldMap = g_Table(
    'CustomFieldMap', metadata,
    g_Column('itemId', Integer, nullable=False, index=True,
             server_default=text("'0'")),
    g_Column('field', String(128), nullable=False),
    g_Column('value', String(255)),
    g_Column('setId', Integer),
    g_Column('setType', Integer)
    )


class DescendentCountsMap(Base):
    userId = Column(Integer, primary_key=True, nullable=False,
                    server_default=text("'0'"))
    itemId = Column(Integer, primary_key=True, nullable=False,
                    server_default=text("'0'"))
    descendentCount = Column(Integer, nullable=False,
                             server_default=text("'0'"))


class EventLogMap(Base):
    id = Column(Integer, primary_key=True)
    userId = Column(Integer)
    type = Column(String(32))
    summary = Column(String(255))
    details = Column(Text)
    location = Column(String(255))
    client = Column(String(128))
    timestamp = Column(Integer, nullable=False, index=True)
    g_referer = Column(String(128))


t_ExifPropertiesMap = g_Table(
    'ExifPropertiesMap', metadata,
    g_Column('property', String(128)),
    g_Column('viewMode', Integer),
    g_Column('sequence', Integer),
    Index('g_property', 'g_property', 'g_viewMode', unique=True)
    )


# Empty
class ExternalIdMap(Base):
    externalId = Column(String(128), primary_key=True, nullable=False)
    entityType = Column(String(32), primary_key=True, nullable=False)
    entityId = Column(Integer, nullable=False, server_default=text("'0'"))


t_FactoryMap = g_Table(
    'FactoryMap', metadata,
    g_Column('classType', String(128)),
    g_Column('className', String(128)),
    g_Column('implId', String(128)),
    g_Column('implPath', String(128)),
    g_Column('implModuleId', String(128)),
    g_Column('hints', String(255)),
    g_Column('orderWeight', String(255))
    )


class FailedLoginsMap(Base):
    userName = Column(String(32), primary_key=True)
    count = Column(Integer, nullable=False)
    lastAttempt = Column(Integer, nullable=False)


class G1MigrateMap(Base):
    itemId = Column(Integer, primary_key=True, server_default=text("'0'"))
    g1album = Column(String(128), nullable=False)
    g1item = Column(String(128))
    __table_args__ = (
        Index('g2_G1MigrateMap_41836', g1album, g1item),
        )


t_Lock = g_Table(
    'Lock', metadata,
    g_Column('lockId', Integer, index=True),
    g_Column('readEntityId', Integer),
    g_Column('writeEntityId', Integer),
    g_Column('freshUntil', Integer),
    g_Column('request', Integer)
    )


class MaintenanceMap(Base):
    runId = Column(Integer, primary_key=True, server_default=text("'0'"))
    taskId = Column(String(128), nullable=False, index=True)
    timestamp = Column(Integer)
    success = Column(Integer)
    details = Column(Text)


class MimeTypeMap(Base):
    extension = Column(String(32), primary_key=True)
    mimeType = Column(String(128))
    viewable = Column(Integer)


t_PluginPackageMap = g_Table(
    'PluginPackageMap', metadata,
    g_Column('pluginType', String(32), nullable=False, index=True),
    g_Column('pluginId', String(32), nullable=False),
    g_Column('packageName', String(32), nullable=False),
    g_Column('packageVersion', String(32), nullable=False),
    g_Column('packageBuild', String(32), nullable=False),
    g_Column('locked', Integer, nullable=False, server_default=text("'0'"))
    )


class RecoverPasswordMap(Base):
    userName = Column(String(32), primary_key=True)
    authString = Column(String(32), nullable=False)
    requestExpires = Column(Integer, nullable=False,
                            server_default=text("'0'"))


class RssMap(Base):
    eedName = Column(String(128), primary_key=True)
    temId = Column(Integer, nullable=False, index=True,
                   server_default=text("'0'"))
    wnerId = Column(Integer, nullable=False, index=True,
                    server_default=text("'0'"))
    arams = Column(Text, nullable=False)


class Schema(Base):
    name = Column(String(128), primary_key=True)
    major = Column(Integer, nullable=False, server_default=text("'0'"))
    minor = Column(Integer, nullable=False, server_default=text("'0'"))
    createSql = Column(Text)
    pluginId = Column(String(32))
    type = Column(String(32))
    info = Column(Text)


t_SequenceEventLog = g_Table(
    'SequenceEventLog', metadata,
    Column('id', Integer, nullable=False)
)


t_SequenceId = g_Table(
    'SequenceId', metadata,
    Column('id', Integer, nullable=False, server_default=text("'0'"))
)


t_SequenceLock = g_Table(
    'SequenceLock', metadata,
    Column('id', Integer, nullable=False, server_default=text("'0'"))
)


class SessionMap(Base):
    id = Column(String(32), primary_key=True)
    userId = Column(Integer, nullable=False, server_default=text("'0'"))
    remoteIdentifier = Column(String(128), nullable=False)
    creationTimestamp = Column(Integer, nullable=False,
                               server_default=text("'0'"))
    modificationTimestamp = Column(Integer, nullable=False,
                                   server_default=text("'0'"))
    data = Column(String)
    __table_args__ = (
        Index('g2_SessionMap_53500',
              userId, creationTimestamp, modificationTimestamp),
        )


class TkOperatnMap(Base):
    name = Column(String(128), primary_key=True)
    parametersCrc = Column(String(32), nullable=False)
    outputMimeType = Column(String(128))
    description = Column(String(255))


t_TkOperatnMimeTypeMap = g_Table(
    'TkOperatnMimeTypeMap', metadata,
    g_Column('operationName', String(128), nullable=False, index=True),
    g_Column('toolkitId', String(128), nullable=False),
    g_Column('mimeType', String(128), nullable=False, index=True),
    g_Column('priority', Integer, nullable=False, server_default=text("'0'"))
    )


t__TkOperatnParameterMap = g_Table(
    'TkOperatnParameterMap', metadata,
    g_Column('operationName', String(128), nullable=False, index=True),
    g_Column('position', Integer, nullable=False, server_default=text("'0'")),
    g_Column('type', String(128), nullable=False),
    g_Column('description', String(255))
    )


t_TkPropertyMap = g_Table(
    'TkPropertyMap', metadata,
    g_Column('name', String(128), nullable=False),
    g_Column('type', String(128), nullable=False),
    g_Column('description', String(128), nullable=False)
)


t_TkPropertyMimeTypeMap = g_Table(
    'TkPropertyMimeTypeMap', metadata,
    g_Column('propertyName', String(128), nullable=False, index=True),
    g_Column('toolkitId', String(128), nullable=False),
    g_Column('mimeType', String(128), nullable=False, index=True)
)


class dbtest0Schema(Base):
    __tablename__ = 'g2dbtest0_Schema'

    name = Column(String(128), primary_key=True, server_default=text("''"))
    major = Column(Integer, nullable=False, server_default=text("'0'"))
    minor = Column(Integer, nullable=False, server_default=text("'0'"))
    testCol = Column(String(128), index=True)


class dbtest1Schema(Base):
    __tablename__ = 'g2dbtest1_Schema'

    name = Column(String(128), primary_key=True, server_default=text("''"))
    major = Column(Integer, nullable=False, server_default=text("'0'"))
    minor = Column(Integer, nullable=False, server_default=text("'0'"))
    testCol = Column(String(128))
