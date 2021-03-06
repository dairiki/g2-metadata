# -*- coding: utf-8 -*-
""" Code for writing gallery metadata usable by sigal_.

.. _sigal: http://sigal.saimon.org/

"""
from __future__ import absolute_import

from collections import OrderedDict, deque
import io
import logging
import os

from six import text_type

from .. import meta
from ..markup import bbcode_to_markdown, strip_bbcode, strip_nl
from ..util import text_, walk_items

log = logging.getLogger(__name__)


def write_markdown(stream, md_text, metadata={}):
    for key, value in metadata.items():
        # ensure it is single-line
        if value is not None:
            stream.write(u"{key:<16s} {value}\n".format(
                key=key.title() + ':',
                value=strip_nl(text_type(value)).strip()))
    stream.write(u"\n")
    if md_text:
        stream.write(text_(md_text))
        stream.write(u"\n")


def zulu(dt):
    if dt:
        return dt.isoformat('T') + 'Z'


class SigalMetadata(object):
    def __init__(self, g2data, albums_path, item):
        self.g2data = g2data
        self.albums_path = albums_path
        self.item = item
        self.target = item.path

    @property
    def target_path(self):
        return os.path.join(self.albums_path, self.target)

    def write_metadata(self):
        md_path = os.path.join(self.albums_path, self.md_path)
        with io.open(md_path, 'w', encoding='utf-8') as fp:
            write_markdown(fp, self.description, self.metadata)

    @property
    def description(self):
        item = self.item
        if item.description:
            return bbcode_to_markdown(item.description)
        else:
            return '\n'

    @property
    def metadata(self):
        # Notes
        # =====

        # In gallery2, ``title`` and ``summary`` are listed in contain
        # album's listing, while ``title`` and ``description`` are
        # listed on the actual item's page.  ``Title`` is interpreted
        # as plain text, while ``summary`` and ``description`` can
        # contain bbcode markup.

        # ``Keywords`` are not displayed anywhere, but are available
        # as search terms.
        item = self.item
        owner = item.owner

        summary = strip_bbcode(item.summary).strip() if item.summary else None
        data = [
            ('title', item.title),
            ('summary', summary),
            # FIXME: use this in the templates (or munge EXIF data?)
            ('date', zulu(item.originationTimestamp)),
            ('created', zulu(item.creationTimestamp)),
            ('updated', zulu(item.modificationTimestamp)),
            ('author', owner.fullName),
            ('author-email', owner.email),
            ('order-weight', item.orderWeight or 0),
            ('gallery2-id', item.id),
            # FIXME: comments?
            ('keywords', item.keywords),
            ('view-count', item.viewCount),
            ('hidden', item.is_hidden and 'yes')
            # XXX: rotation information?
            ]
        return OrderedDict((k, v) for k, v in data if v is not None)

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

    def _find_hilight(self):
        """ Find hilight for item.

        If item does not have an explicit hilight, check subitems, in
        order, for one that has an explicit or implicit hilight.

        """
        traverse = deque([self.item])
        while traverse:
            item = traverse.popleft()
            if item.hilight:
                return item.hilight
            traverse.extendleft(reversed(item.subitems))

    @property
    def metadata(self):
        item = self.item
        data = super(SigalAlbumHelper, self).metadata
        hilight = self._find_hilight()
        if hilight is not None:
            # XXX: What if the hilight item is hidden (or in a hidden
            # album)?
            hilight_path = os.path.join(self.albums_path, hilight.path)
            thumbnail = os.path.relpath(hilight_path, self.target_path)
            if not os.path.exists(hilight_path):
                log.warning("%s: thumbnail %s does not exist",
                            self.target, thumbnail)
            data['thumbnail'] = thumbnail

        core_params = self.g2data['plugin_parameters']['module']['core']
        if item.orderBy:
            order_by = item.orderBy
            order_direction = item.orderDirection
        else:
            order_by = core_params.get('default.orderBy')
            order_direction = core_params.get('default.orderDirection')
        if order_by:
            data['order-by'] = order_by
            # Normalize order direction.  (It is either exactly 'desc' or
            # g2 interprets is as 'asc'.)
            data['order-direction'] = '|'.join(
                'desc' if od.strip() == 'desc' else 'asc'
                for od in (order_direction or '').split('|'))

        return data

    def check_target(self):
        if not os.path.isdir(self.target_path):
            log.error("%s: not a directory", self.target)
        else:
            super(SigalAlbumHelper, self).check_target()


def write_metadata(g2data, albums_path):
    album = g2data['album']
    for item in walk_items(album):
        if isinstance(item, meta.AlbumItem):
            helper = SigalAlbumHelper(g2data, albums_path, item)
        elif isinstance(item, (meta.PhotoItem, meta.MovieItem)):
            helper = SigalImageHelper(g2data, albums_path, item)
        else:
            log.warning("Do not know how to handle %r.  Ignoring..." % item)
            continue
        log.debug("Processing {0.path}".format(item))
        helper.check_target()
        helper.write_metadata()
