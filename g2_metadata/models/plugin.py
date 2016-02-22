# coding: utf-8
""" Plugin metadata

This includes the "plugin parameters".  Note that the ``core`` module is a
"plugin" whose paramters provide global settings for the gallery.

"""
from itertools import groupby
from operator import attrgetter

import phpserialize
from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
    )

from .base import Base
from .entity import Entity

class PluginMap(Base):
    pluginType = Column(String(32), primary_key=True, nullable=False)
    pluginId = Column(String(32), primary_key=True, nullable=False)
    active = Column(Integer, nullable=False, server_default=text("'0'"))


class PluginParameterMap(Base):
    pluginType = Column(String(32), primary_key=True, nullable=False)
    pluginId = Column(String(32), primary_key=True, nullable=False)
    itemId = Column(ForeignKey(Entity.id), primary_key=True, nullable=False,
                    server_default=text("'0'"))

    parameterName = Column(String(128), primary_key=True, nullable=False)
    parameterValue = Column(Text, nullable=False)

    __table_args__ = (
        Index('g2_PluginParameterMap_12808', pluginType, pluginId, itemId),
        )


# NB: See also t_PluginPackageMap in .cruft which we are currently not using.


def get_global_plugin_parameters(session):
    """ Get nested dict containing all the global plugin paramters.

    """
    return plugin_parameters_to_dict(
        session.query(PluginParameterMap).filter_by(itemId=0))


def plugin_parameters_to_dict(plugin_parameters):
    """ Convert a sequence of ``PluginParamterMap`` instances to nested dict.

    Values which look to be phpserialized are unserialized.

    """
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
