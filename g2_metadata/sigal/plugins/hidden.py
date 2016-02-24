# -*- coding: utf-8 -*-
""" Plugin to omit albums and media who have the "Hidden" metadata set

This omits generating any gallery products for albums or media which have::

    Hidden: yes

or similar set in their sigal metadata (.md) file.

"""
from __future__ import absolute_import

from collections import Counter, defaultdict, deque

from sigal import signals


def is_hidden(obj):
    hidden = '\n'.join(obj.meta.get('hidden', []))
    return hidden.strip().lower() in ('y', 'yes', 't', 'true')


def walk_subalbums(album):
    albums = deque(album.albums)
    while albums:
        albums.extend(albums[0].albums)
        yield albums.popleft()


def after_album_initialized(album):
    logger = album.logger
    gallery = album.gallery

    if is_hidden(album):
        logger.info("Ignoring hidden album: %s", album)
        # Since sigal scans directories depth-first, our subalbums have already
        # been scanned.  We need to remove sigal's memory of them.
        for subalbum in walk_subalbums(album):
            del gallery.albums[subalbum.path]
        # Empty ourself out.  Sigal ignores empty albums.
        album.subdirs = []
        album.medias = []
    else:
        # Filter out hidden medias
        visible_medias = []
        for media in album.medias:
            if is_hidden(media):
                logger.info("Ignoring hidden media: %s", media)
            else:
                visible_medias.append(media)
        album.medias = visible_medias

    # Fixup media counts
    counts = Counter(media.type for media in album.medias)
    album.medias_count = defaultdict(int, counts)


def register(settings):
    signals.album_initialized.connect(after_album_initialized)
