# -*- coding: utf-8 -*-
""" Code for writing gallery metadata usable by sigal_.

.. _sigal: http://sigal.saimon.org/

"""
from __future__ import absolute_import

from collections import OrderedDict
import io
import logging
import os
import re

from . import meta
from .markup import bbcode_to_markdown, strip_bbcode
from .util import text_, walk_items

log = logging.getLogger(__name__)


def write_markdown(stream, md_text, metadata={}):
    for key in metadata:
        # ensure it is single-line
        value = re.sub(r'\s*\n\s*', ' ', metadata[key])
        stream.write(u"{0:<8s} {1}\n".format("%s:" % key.title(), value))
    stream.write(u"\n")
    if md_text:
        stream.write(text_(md_text))
        stream.write(u"\n")


def normalize_summary(item):
    """ Try to make summary superfluous.

    Gallery items have a title, summary and description.  Sigal, like most
    other galleries has only title and description.

    Here we try to reduce the information in (title, summary, description)
    down to just (title, description).

    """
    title = item.title
    summary = item.summary
    description = item.description
    fn = item.pathComponent or ''
    fnbase = os.path.splitext(fn)[0]

    # FIXME: bbcode can only be in description
    # FIXME: deal with bbcode in summary (and title?)

    if title in (fn, fnbase):
        title = None
    if summary in (fn, fnbase, title, description):
        summary = None
    if description in (fn, fnbase, title):
        description = None

    if summary and not title:
        title, summary = strip_bbcode(summary), None
    elif summary and not description:
        description, summary = summary, None

    if summary:
        log.warning(
            "Can not eliminate non-trivial summary.\n"
            "  title   = {title!r}\n"
            "  summary = {summary!r}\n"
            "  description = {description!r}".format(**locals()))

    if not title:
        title = fnbase

    if summary:
        summary = strip_bbcode(summary)
    if description:
        description = bbcode_to_markdown(description)

    return title, summary, description


class SigalMetadata(object):
    # FIXME: convert bbcode in description to markdown
    def __init__(self, albums_path, item):
        self.albums_path = albums_path
        self.item = item
        self.target = item.path
        self.title, self.summary, self.description = normalize_summary(item)

    def write_metadata(self):
        metadata = self.metadata.copy()
        description = metadata.pop('description', None)
        md_path = os.path.join(self.albums_path, self.md_path)
        log.info("Writing metadata to {0.md_path}".format(self))
        with io.open(md_path, 'w', encoding='utf-8') as fp:
            write_markdown(fp, description, metadata)

    @property
    def metadata(self):
        item = self.item
        owner = item.owner
        date = item.originationTimestamp
        if date:
            date = date.isoformat() + 'Z'
        data = [
            ('title', self.title),
            ('summary', self.summary),
            ('description', self.description),
            ('date', item.originationTimestamp),  # FIXME: format to local time?
            ('author', owner.fullName),
            ('author-email', owner.email),
            # FIXME: what if album is order by other keys?
            # FIXME: what if no orderWeight?
            ('order', item.orderWeight or 0),
            ('gallery2-id', item.id),
            # FIXME: comments?
            # FIXME: thumbnail!
            # FIXME: keywords
            # FIXME: original title, summary, description?
            # FIXME: hidden flag
            # FIXME: rotation information?
            ]
        data = OrderedDict((k, unicode(v)) for k, v in data if v is not None)
        if not data:
            data = {'title': item.pathComponent}
        return data


class SigalImageHelper(SigalMetadata):
    @property
    def md_path(self):
        base, ext = os.path.splitext(self.target)
        return base + '.md'


class SigalAlbumHelper(SigalMetadata):
    @property
    def md_path(self):
        return os.path.join(self.target, 'index.md')

    @property
    def metadata(self):
        data = super(SigalAlbumHelper, self).metadata
        item = self.item
        hilight = item.hilight
        if hilight is not None:
            hilight_path = hilight.pathComponent
            parent = hilight.parent
            while parent != item:
                assert parent is not None
                hilight_path = os.path.join(parent.pathComponent, hilight_path)
                parent = parent.parent
            data['thumbnail'] = hilight_path
        else:
            # FIXME: Check that sigal picks first subitem for thumbnail.
            # If not, we'll have to pick it ourself here.
            pass

        return data


def write_metadata(data, albums_path):
    album = data['album']
    for item in walk_items(album):
        if isinstance(item, meta.AlbumItem):
            helper = SigalAlbumHelper(albums_path, item)
        elif isinstance(item, (meta.PhotoItem, meta.MovieItem)):
            helper = SigalImageHelper(albums_path, item)
            # FIXME: ensure symlink exists, if needed
        else:
            log.warning("Do not know how to handle %r.  Ignoring..." % item)
            continue
        log.debug("Processing {0.path}".format(item))
        helper.write_metadata()
