# -*- coding: utf-8 -*-
""" Plugin to sort albums and media the way they were ordered in gallery2.

"""
from __future__ import absolute_import

import os

from sigal import signals


def order(obj):
    try:
        return int('\n'.join(obj.meta.get('order', [])))
    except ValueError:
        return 0


def resort_subdirs(album):
    gallery = album.gallery
    settings = album.settings
    root_path = album.path if album.path != '.' else ''

    def subalbum(subdir):
        return gallery.albums[os.path.join(root_path, subdir)]

    album.subdirs.sort(key=lambda subdir: order(subalbum(subdir)),
                       reverse=settings['albums_sort_reverse'])


def resort_medias(album):
    settings = album.settings
    album.medias.sort(key=order, reverse=settings['medias_sort_reverse'])


def register(settings):
    signals.albums_sorted.connect(resort_subdirs)
    signals.medias_sorted.connect(resort_medias)
