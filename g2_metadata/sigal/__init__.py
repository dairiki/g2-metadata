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

from .. import meta
from ..markup import bbcode_to_markdown, strip_bbcode
from ..util import text_, walk_items

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

    if title in (fn, fnbase):
        title = None
    if summary in (fn, fnbase, title, description):
        summary = None
    if description in (fn, fnbase, title):
        description = None

    # NB: In gallery2, the summary can contain bbcode markup, while the
    # title is always just plain text.  So be careful to strip markup
    # if moving the summary to the title.
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

    # For sigal, the title and summary should be plain text (though
    # the summary is currently ignored.)  The description is parsed as
    # markdown.
    if summary:
        summary = strip_bbcode(summary)
    if description:
        description = bbcode_to_markdown(description)

    return title, summary, description


class SigalMetadata(object):
    def __init__(self, albums_path, item):
        self.albums_path = albums_path
        self.item = item
        self.target = item.path
        self.title, self.summary, self.description = normalize_summary(item)

    @property
    def target_path(self):
        return os.path.join(self.albums_path, self.target)

    def write_metadata(self):
        metadata = self.metadata.copy()
        description = metadata.pop('description', None)
        md_path = os.path.join(self.albums_path, self.md_path)
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
            # FIXME: what if album is ordered by other keys?
            ('order', item.orderWeight or 0),
            ('gallery2-id', item.id),
            # FIXME: comments?
            ('keywords', item.keywords),
            # FIXME: hidden flag
            ('hidden', item.is_hidden and 'yes')
            # FIXME: original title, summary, description?
            # FIXME: rotation information?
            ]
        data = OrderedDict((k, unicode(v)) for k, v in data if v is not None)
        if not data:
            data = {'title': item.pathComponent}
        return data

    def check_target(self):
        target_path = self.target_path
        if not os.path.exists(target_path):
            log.error("%s: target does not exist", self.target)
        elif not os.access(target_path, os.R_OK):
            log.warning("%s: is not readable", self.target)


class SigalImageHelper(SigalMetadata):
    @property
    def md_path(self):
        base, ext = os.path.splitext(self.target)
        return base + '.md'

    def _check_link(self):
        target_path = self.target_path
        link = self.item.linked_item.path
        link_path = os.path.join(self.albums_path, link)

        if not os.path.exists(target_path):
            # Create symlink
            if os.path.isfile(link_path):
                link_relpath = os.path.relpath(link_path,
                                               os.path.dirname(target_path))
                log.info("%s: creating symlink link to %s",
                         self.target, link_relpath)
                os.symlink(link_relpath, target_path)
            else:
                log.error("%s: link target %s is not a regular file",
                          self.target, link)
        elif not os.path.islink(target_path):
            log.warning("%s: not a symlink", self.target)

    def check_target(self):
        if self.item.linked_item is not None:
            self._check_link()
        super(SigalImageHelper, self).check_target()


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

    def check_target(self):
        if not os.path.isdir(self.target_path):
            log.error("%s: not a directory", self.target)
        else:
            super(SigalAlbumHelper, self).check_target()


def write_metadata(data, albums_path):
    album = data['album']
    for item in walk_items(album):
        if isinstance(item, meta.AlbumItem):
            helper = SigalAlbumHelper(albums_path, item)
        elif isinstance(item, (meta.PhotoItem, meta.MovieItem)):
            helper = SigalImageHelper(albums_path, item)
        else:
            log.warning("Do not know how to handle %r.  Ignoring..." % item)
            continue
        log.debug("Processing {0.path}".format(item))
        helper.check_target()
        helper.write_metadata()
