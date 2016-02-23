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
from sqlalchemy.orm import relationship

from .base import metadata, g_Column, g_Table
from .entity import (
    ChildEntity,
    Entity,
    )


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
