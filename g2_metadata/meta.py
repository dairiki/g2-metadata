# -*- coding: utf-8 -*-
""" Dummy versions of the ORM-mapped classes in .models.

These are plain jane classes with the same names and inheritance
tree as those in ``g2_metadata.models``.

"""
# flake8: noqa

# in .models.entity
class Entity(object):
    def __repr__(self):
        return "<%s id=%d>" % (self.__class__.__name__, self.id)

class ChildEntity(Entity): pass
class FileSystemEntity(ChildEntity): pass
class Comment(ChildEntity): pass
class ThumbnailImage(FileSystemEntity): pass


# in .models.item
class Item(FileSystemEntity): pass
class AlbumItem(Item): pass
class PhotoItem(Item): pass
class MovieItem(Item): pass
class LinkItem(Item): pass
class AnimationItem(Item): pass
class DataItem(Item): pass
class UnknownItem(Item): pass

# in .models.access
class User(Entity): pass
class Group(Entity): pass
class AccessMap(object): pass
class AccessSubscriberMap(object): pass

# in .models.derivative
class Derivative(ChildEntity): pass
class DerivativeImage(Derivative): pass
