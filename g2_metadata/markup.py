# -*- coding: utf-8 -*-
""" Markup conversion utilities

Note that Gallery2 seems to support only the following bbcode tags:

[list]
[*] List item
[/list]
[b], [i]
[url]example.com[/url], [url=http...]label[/url]
[color=green]green[/color], [color=#12fe23]foo[/color]
[img]http:...[/img] (support width, height attributes)

"""
from __future__ import absolute_import

import re

import bbcode
from html2text import HTML2Text


bbcode_parser = bbcode.Parser(escape_html=False)


def _render_img(name, value, options, parent, context):
    size = ''
    if options:
        for attr in 'width', 'height':
            dim = options.get(attr)
            if dim is not None:
                try:
                    dim = int(dim)
                except ValueError:
                    pass
                else:
                    size += ' %s="%d"' % (attr, dim)
    return '<img src="%s" alt=""%s />' % (value, size)

bbcode_parser.add_formatter('img', _render_img,
                            same_tag_closes=True,
                            render_embedded=False,
                            transform_newlines=False,
                            escape_html=True,
                            replace_cosmetic=False,
                            replace_links=False,
                            strip=True)


def bbcode_to_markdown(text):
    # FIXME: text = text_(text)
    html = bbcode_parser.format(text)
    h2t = HTML2Text()
    # FIXME: options
    return h2t.handle(html)


def strip_bbcode(text, strip_newlines=True):
    # FIXME: text = text_(text)
    # passing strip_newlines to strip, really strips them (not putting any spaces
    # in to replace them)
    stripped = bbcode_parser.strip(text, strip_newlines=False)
    if strip_newlines:
        stripped = re.sub(r'\s*\n\s*', ' ', stripped)
    return stripped
