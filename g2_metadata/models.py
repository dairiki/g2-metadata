# coding: utf-8
from calendar import timegm
from datetime import datetime
from itertools import groupby
from operator import attrgetter
import os

import phpserialize
from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    TypeDecorator,
    event,
    inspect,
    text,
    )
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


class Timestamp(TypeDecorator):
    impl = Integer

    def process_bind_param(self, value, dialect):
        if isinstance(value, datetime):
            return timegm(value.utctimetuple())
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return datetime.utcfromtimestamp(value)


@event.listens_for(Base, 'instrument_class', propagate=True)
def _instrument_class(mapper, cls):
    """ Prefix all non-explicit column names with ``'g_``
    """
    for attr, column in cls.__dict__.items():
        if isinstance(column, Column):
            if column.name == attr:
                column.name = 'g_' + attr


class Entity(Base):
    __tablename__ = 'g2_Entity'
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
        return _plugin_parameters_to_dict(self._plugin_parameters)

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
    __tablename__ = 'g2_ChildEntity'

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
    __tablename__ = 'g2_FileSystemEntity'

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
    __tablename__ = 'g2_Comment'
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
    __tablename__ = 'g2_ThumbnailImage'
    __mapper_args__ = {'polymorphic_identity': 'ThumbnailImage'}

    id = Column(Integer, ForeignKey(FileSystemEntity.id), primary_key=True)
    mimeType = Column(String(128))
    size = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    itemMimeTypes = Column(String(128))


t_Item = Table(
    'g2_Item', metadata,
    Column('g_id', ForeignKey(FileSystemEntity.id),
           primary_key=True,
           server_default=text("'0'"),
           key='id'),
    Column('g_canContainChildren', Integer,
           nullable=False, server_default=text("'0'"),
           key='canContainChildren'),
    Column('g_description', Text,
           key='description'),
    Column('g_keywords', String(255), index=True,
           key='keywords'),
    Column('g_ownerId', Integer, nullable=False,
           index=True, server_default=text("'0'"),
           key='ownerId'),
    Column('g_summary', String(255), index=True,
           key='summary'),
    Column('g_title', String(128), index=True,
           key='title'),
    Column('g_viewedSinceTimestamp', Timestamp,
           nullable=False,
           server_default=text("'0'"),
           key='viewedSinceTimestamp'),
    Column('g_originationTimestamp', Timestamp,
           nullable=False,
           server_default=text("'0'"),
           key='originationTimestamp'),
    Column('g_renderer', String(128),
           key='renderer'),
    )

t_ItemAttributesMap = Table(
    'g2_ItemAttributesMap', metadata,
    Column('g_itemId', ForeignKey(t_Item.c.id),
           primary_key=True, server_default=text("'0'"),
           key='_attributes_id'),
    Column('g_viewCount', Integer,
           key='viewCount'),
    Column('g_orderWeight', Integer,
           key='orderWeight'),
    Column('g_parentSequence', String(255), nullable=False, index=True,
           key='parentSequence'),
    )

t_ItemHiddenMap = Table(
    'g2_ItemHiddenMap', metadata,
    Column('g_itemId', ForeignKey(t_Item.c.id), primary_key=True,
           key='_hidden_id'),
    )


class Item(FileSystemEntity):
    __table__ = t_Item.outerjoin(t_ItemAttributesMap)\
                      .outerjoin(t_ItemHiddenMap)

    @property
    def is_hidden(self):
        return self._hidden_id is not None

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
    __tablename__ = 'g2_AlbumItem'
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
    __tablename__ = 'g2_PhotoItem'
    __mapper_args__ = {'polymorphic_identity': 'GalleryPhotoItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))
    width = Column(Integer)
    height = Column(Integer)


class MovieItem(Item):
    __tablename__ = 'g2_MovieItem'
    __mapper_args__ = {'polymorphic_identity': 'GalleryMovieItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))
    width = Column(Integer)
    height = Column(Integer)
    duration = Column(Integer)


class LinkItem(Item):
    __tablename__ = 'g2_LinkItem'
    __mapper_args__ = {'polymorphic_identity': 'GalleryLinkItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))
    link = Column(Text, nullable=False)


class AnimationItem(Item):
    __tablename__ = 'g2_AnimationItem'
    __mapper_args__ = {'polymorphic_identity': 'GalleryAnimationItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))
    width = Column(Integer)
    height = Column(Integer)


class DataItem(Item):
    __tablename__ = 'g2_DataItem'
    __mapper_args__ = {'polymorphic_identity': 'GalleryDataItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))
    mimeType = Column(String(128))
    size = Column(Integer)


class UnknownItem(Item):
    __tablename__ = 'g2_UnknownItem'
    __mapper_args__ = {'polymorphic_identity': 'GalleryUnknownItem'}

    id = Column(ForeignKey(Item.id), primary_key=True,
                server_default=text("'0'"))


class Derivative(ChildEntity):
    __tablename__ = 'g2_Derivative'
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
    __tablename__ = 'g2_DerivativeImage'
    __mapper_args__ = {'polymorphic_identity': 'GalleryDerivativeImage'}

    id = Column(ForeignKey(Derivative.id),
                primary_key=True, server_default=text("'0'"))
    width = Column(Integer)
    height = Column(Integer)


t_g2_DerivativePrefsMap = Table(
    'g2_DerivativePrefsMap', metadata,
    Column('g_itemId', Integer, index=True),
    Column('g_order', Integer),
    Column('g_derivativeType', Integer),
    Column('g_derivativeOperations', String(255))
)


class User(Entity):
    __tablename__ = 'g2_User'
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
    __tablename__ = 'g2_Group'
    __mapper_args__ = {'polymorphic_identity': 'GalleryGroup'}

    id = Column(ForeignKey(Entity.id), primary_key=True,
                server_default=text("'0'"))
    groupType = Column(Integer, nullable=False, server_default=text("'0'"))
    groupName = Column(String(128), unique=True)


t_UserGroupMap = Table(
    'g2_UserGroupMap', metadata,
    Column('g_userId', ForeignKey(User.id), nullable=False, index=True,
           server_default=text("'0'")),
    Column('g_groupId', ForeignKey(Group.id), nullable=False, index=True,
           server_default=text("'0'")),
    )

Group.users = relationship(User, secondary=t_UserGroupMap, backref='groups')


class PluginMap(Base):
    __tablename__ = 'g2_PluginMap'

    pluginType = Column(String(32), primary_key=True, nullable=False)
    pluginId = Column(String(32), primary_key=True, nullable=False)
    active = Column(Integer, nullable=False, server_default=text("'0'"))


t_g2_PluginPackageMap = Table(
    'g2_PluginPackageMap', metadata,
    Column('g_pluginType', String(32), nullable=False, index=True),
    Column('g_pluginId', String(32), nullable=False),
    Column('g_packageName', String(32), nullable=False),
    Column('g_packageVersion', String(32), nullable=False),
    Column('g_packageBuild', String(32), nullable=False),
    Column('g_locked', Integer, nullable=False, server_default=text("'0'"))
)


class PluginParameterMap(Base):
    __tablename__ = 'g2_PluginParameterMap'
    pluginType = Column(String(32), primary_key=True, nullable=False)
    pluginId = Column(String(32), primary_key=True, nullable=False)
    itemId = Column(ForeignKey(Entity.id), primary_key=True,
                    nullable=False,
                    server_default=text("'0'"))

    parameterName = Column(String(128), primary_key=True, nullable=False)
    parameterValue = Column(Text, nullable=False)

    __table_args__ = (
        Index('g2_PluginParameterMap_12808', pluginType, pluginId, itemId),
        )


def _neaten_php_value(value):
    # Convert things that looks like lists back to lists
    #
    # Also convert empty dicts to ``None``
    #
    if isinstance(value, dict):
        if len(value) == 0:
            return None
        elif set(value.keys()) == set(range(len(value))):
            return [_neaten_php_value(value[i]) for i in range(len(value))]
    return value


def _maybe_php_deserialize(value):
    try:
        value = phpserialize.loads(value)
    except ValueError:
        return value
    else:
        value = _neaten_php_value(value)


def _plugin_parameters_to_dict(plugin_parameters):
    parameters = sorted(plugin_parameters,
                        key=attrgetter('pluginType', 'pluginId'))
    by_plugin = {}
    for ptype, pt_params in groupby(parameters, attrgetter('pluginType')):
        by_plugin[ptype] = {}
        for pid, params in groupby(pt_params, attrgetter('pluginId')):
            items = map(attrgetter('parameterName', 'parameterValue'),
                        params)
            pdict = dict((name, _maybe_php_deserialize(value))
                         for name, value in items)
            by_plugin[ptype][pid] = pdict
        return by_plugin


def get_global_plugin_parameters(session):
    return _plugin_parameters_to_dict(
        session.query(PluginParameterMap).filter_by(itemId=0))


class AccessMap(Base):
    __tablename__ = 'g2_AccessMap'

    g_accessListId = Column(Integer, primary_key=True, nullable=False, index=True, server_default=text("'0'"))
    g_permission = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    g_userOrGroupId = Column(Integer, primary_key=True, nullable=False, index=True, server_default=text("'0'"))


class AccessSubscriberMap(Base):
    __tablename__ = 'g2_AccessSubscriberMap'

    g_itemId = Column(Integer, primary_key=True, server_default=text("'0'"))
    g_accessListId = Column(Integer, nullable=False, index=True, server_default=text("'0'"))


class CacheMap(Base):
    # b_type is always 'page'
    __tablename__ = 'g2_CacheMap'
    __table_args__ = (
        Index('g2_CacheMap_21979', 'g_userId', 'g_timestamp', 'g_isEmpty'),
    )

    g_key = Column(String(32), primary_key=True, nullable=False)
    g_value = Column(String)
    g_userId = Column(Integer, primary_key=True, nullable=False, server_default=text("'0'"))
    g_itemId = Column(Integer, primary_key=True, nullable=False, index=True, server_default=text("'0'"))
    g_type = Column(String(32), primary_key=True, nullable=False)
    g_timestamp = Column(Integer, nullable=False, server_default=text("'0'"))
    g_isEmpty = Column(Integer)


# Empty
# t_g2_CustomFieldMap = Table(
#     'g2_CustomFieldMap', metadata,
#     Column('g_itemId', Integer, nullable=False, index=True, server_default=text("'0'")),
#     Column('g_field', String(128), nullable=False),
#     Column('g_value', String(255)),
#     Column('g_setId', Integer),
#     Column('g_setType', Integer)
# )


class DescendentCountsMap(Base):
    __tablename__ = 'g2_DescendentCountsMap'

    g_userId = Column(Integer, primary_key=True, nullable=False, server_default=text("'0'"))
    g_itemId = Column(Integer, primary_key=True, nullable=False, server_default=text("'0'"))
    g_descendentCount = Column(Integer, nullable=False, server_default=text("'0'"))




class EventLogMap(Base):
    __tablename__ = 'g2_EventLogMap'

    g_id = Column(Integer, primary_key=True)
    g_userId = Column(Integer)
    g_type = Column(String(32))
    g_summary = Column(String(255))
    g_details = Column(Text)
    g_location = Column(String(255))
    g_client = Column(String(128))
    g_timestamp = Column(Integer, nullable=False, index=True)
    g_referer = Column(String(128))


t_g2_ExifPropertiesMap = Table(
    'g2_ExifPropertiesMap', metadata,
    Column('g_property', String(128)),
    Column('g_viewMode', Integer),
    Column('g_sequence', Integer),
    Index('g_property', 'g_property', 'g_viewMode', unique=True)
)


# Empty
# class ExternalIdMap(Base):
#     __tablename__ = 'g2_ExternalIdMap'

#     g_externalId = Column(String(128), primary_key=True, nullable=False)
#     g_entityType = Column(String(32), primary_key=True, nullable=False)
#     g_entityId = Column(Integer, nullable=False, server_default=text("'0'"))


t_g2_FactoryMap = Table(
    'g2_FactoryMap', metadata,
    Column('g_classType', String(128)),
    Column('g_className', String(128)),
    Column('g_implId', String(128)),
    Column('g_implPath', String(128)),
    Column('g_implModuleId', String(128)),
    Column('g_hints', String(255)),
    Column('g_orderWeight', String(255))
)


class FailedLoginsMap(Base):
    __tablename__ = 'g2_FailedLoginsMap'

    g_userName = Column(String(32), primary_key=True)
    g_count = Column(Integer, nullable=False)
    g_lastAttempt = Column(Integer, nullable=False)


class G1MigrateMap(Base):
    __tablename__ = 'g2_G1MigrateMap'
    __table_args__ = (
        Index('g2_G1MigrateMap_41836', 'g_g1album', 'g_g1item'),
    )

    g_itemId = Column(Integer, primary_key=True, server_default=text("'0'"))
    g_g1album = Column(String(128), nullable=False)
    g_g1item = Column(String(128))


t_g2_Lock = Table(
    'g2_Lock', metadata,
    Column('g_lockId', Integer, index=True),
    Column('g_readEntityId', Integer),
    Column('g_writeEntityId', Integer),
    Column('g_freshUntil', Integer),
    Column('g_request', Integer)
)


class MaintenanceMap(Base):
    __tablename__ = 'g2_MaintenanceMap'

    g_runId = Column(Integer, primary_key=True, server_default=text("'0'"))
    g_taskId = Column(String(128), nullable=False, index=True)
    g_timestamp = Column(Integer)
    g_success = Column(Integer)
    g_details = Column(Text)


class MimeTypeMap(Base):
    __tablename__ = 'g2_MimeTypeMap'

    g_extension = Column(String(32), primary_key=True)
    g_mimeType = Column(String(128))
    g_viewable = Column(Integer)


t_g2_PermissionSetMap = Table(
    'g2_PermissionSetMap', metadata,
    Column('g_module', String(128), nullable=False),
    Column('g_permission', String(128), nullable=False, unique=True),
    Column('g_description', String(255)),
    Column('g_bits', Integer, nullable=False, server_default=text("'0'")),
    Column('g_flags', Integer, nullable=False, server_default=text("'0'"))
)


class RecoverPasswordMap(Base):
    __tablename__ = 'g2_RecoverPasswordMap'

    g_userName = Column(String(32), primary_key=True)
    g_authString = Column(String(32), nullable=False)
    g_requestExpires = Column(Integer, nullable=False, server_default=text("'0'"))


class RssMap(Base):
    __tablename__ = 'g2_RssMap'

    g_feedName = Column(String(128), primary_key=True)
    g_itemId = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    g_ownerId = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    g_params = Column(Text, nullable=False)


class Schema(Base):
    __tablename__ = 'g2_Schema'

    g_name = Column(String(128), primary_key=True)
    g_major = Column(Integer, nullable=False, server_default=text("'0'"))
    g_minor = Column(Integer, nullable=False, server_default=text("'0'"))
    g_createSql = Column(Text)
    g_pluginId = Column(String(32))
    g_type = Column(String(32))
    g_info = Column(Text)


t_g2_SequenceEventLog = Table(
    'g2_SequenceEventLog', metadata,
    Column('id', Integer, nullable=False)
)


t_g2_SequenceId = Table(
    'g2_SequenceId', metadata,
    Column('id', Integer, nullable=False, server_default=text("'0'"))
)


t_g2_SequenceLock = Table(
    'g2_SequenceLock', metadata,
    Column('id', Integer, nullable=False, server_default=text("'0'"))
)


class SessionMap(Base):
    __tablename__ = 'g2_SessionMap'
    __table_args__ = (
        Index('g2_SessionMap_53500', 'g_userId', 'g_creationTimestamp', 'g_modificationTimestamp'),
    )

    g_id = Column(String(32), primary_key=True)
    g_userId = Column(Integer, nullable=False, server_default=text("'0'"))
    g_remoteIdentifier = Column(String(128), nullable=False)
    g_creationTimestamp = Column(Integer, nullable=False, server_default=text("'0'"))
    g_modificationTimestamp = Column(Integer, nullable=False, server_default=text("'0'"))
    g_data = Column(String)


class TkOperatnMap(Base):
    __tablename__ = 'g2_TkOperatnMap'

    g_name = Column(String(128), primary_key=True)
    g_parametersCrc = Column(String(32), nullable=False)
    g_outputMimeType = Column(String(128))
    g_description = Column(String(255))


t_g2_TkOperatnMimeTypeMap = Table(
    'g2_TkOperatnMimeTypeMap', metadata,
    Column('g_operationName', String(128), nullable=False, index=True),
    Column('g_toolkitId', String(128), nullable=False),
    Column('g_mimeType', String(128), nullable=False, index=True),
    Column('g_priority', Integer, nullable=False, server_default=text("'0'"))
)


t_g2_TkOperatnParameterMap = Table(
    'g2_TkOperatnParameterMap', metadata,
    Column('g_operationName', String(128), nullable=False, index=True),
    Column('g_position', Integer, nullable=False, server_default=text("'0'")),
    Column('g_type', String(128), nullable=False),
    Column('g_description', String(255))
)


t_g2_TkPropertyMap = Table(
    'g2_TkPropertyMap', metadata,
    Column('g_name', String(128), nullable=False),
    Column('g_type', String(128), nullable=False),
    Column('g_description', String(128), nullable=False)
)


t_g2_TkPropertyMimeTypeMap = Table(
    'g2_TkPropertyMimeTypeMap', metadata,
    Column('g_propertyName', String(128), nullable=False, index=True),
    Column('g_toolkitId', String(128), nullable=False),
    Column('g_mimeType', String(128), nullable=False, index=True)
)




class dbtest0Schema(Base):
    __tablename__ = 'g2dbtest0_Schema'

    g_name = Column(String(128), primary_key=True, server_default=text("''"))
    g_major = Column(Integer, nullable=False, server_default=text("'0'"))
    g_minor = Column(Integer, nullable=False, server_default=text("'0'"))
    g_testCol = Column(String(128), index=True)


class dbtest1Schema(Base):
    __tablename__ = 'g2dbtest1_Schema'

    g_name = Column(String(128), primary_key=True, server_default=text("''"))
    g_major = Column(Integer, nullable=False, server_default=text("'0'"))
    g_minor = Column(Integer, nullable=False, server_default=text("'0'"))
    g_testCol = Column(String(128))


def _fix_nl(s):
    if isinstance(s, basestring):
        return s.replace('\r\n', '\n')
    return s

def _fmt_timestamp(ts):
    if ts is None:
        return None
    dt = datetime.utcfromtimestamp(ts)
    return dt.isoformat() + 'Z'
