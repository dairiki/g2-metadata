# -*- coding: utf-8 -*-
""" Plugin to normalize {title, summary, description}

"""
from __future__ import absolute_import

import os
import re

from sigal import signals


def _canonize(s):
    return re.sub(r'[^\w]', '_', s.strip())


def normalize(item):
    summary = item.meta.get('summary', [''])[0].strip()

    fn = os.path.basename(item.path)
    fnbase = os.path.splitext(fn)[0]
    trivial_titles = _canonize(fn), _canonize(fnbase)

    def is_trivial(s):
        return not s or _canonize(s) in trivial_titles

    if not is_trivial(summary):
        if summary != item.title and is_trivial(item.title):
            item.logger.info("Replacing title with summary for %s\n"
                             "    was: %r\n"
                             "    now: %r",
                             item, item.title, summary)
            item.title = summary

        description = item.description
        is_dup = description == item.title
        if summary != description and (is_trivial(description) or is_dup):
            item.logger.info("Replacing description with summary for %s\n"
                             "    was: %r\n"
                             "    now: %r",
                             item, item.description, summary)
            item.description = summary
        elif is_dup:
            item.logger.info("Clearing description with matches title for %s\n"
                             "    was: %r",
                             item, item.description)
            item.description = ''


def register(settings):
    signals.album_initialized.connect(normalize)
    signals.media_initialized.connect(normalize)
