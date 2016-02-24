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
import jinja2
from markdown import markdown
from pkg_resources import resource_string

from .util import text_, walk_items


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
    html = bbcode_parser.format(text_(text))
    h2t = HTML2Text()
    h2t.unicode_snob = True
    return h2t.handle(html)


def strip_bbcode(text, strip_newlines=True):
    # NB: We have to do the newline stripping ourself. Passing
    # strip_newlines=True to bbcode.Parser.strip really strips them
    # completely — it doesn’t put any spaces in to replace them.
    stripped = bbcode_parser.strip(text_(text), strip_newlines=False)
    if strip_newlines:
        stripped = re.sub(r'\s*\n\s*', ' ', stripped)
    return stripped


def make_bbcode_test_page(metadata, outfp):
    samples = []
    for item in walk_items(metadata['album']):
        for attr in 'title', 'summary', 'description':
            s = text_(getattr(item, attr))
            if s and re.search(r'\[\w+.*\]|\n', s.strip()):
                # Looks like bbcode
                md = bbcode_to_markdown(s)
                samples.append({
                    'path': item.path,
                    'field': attr,
                    'bbcode': s,
                    'stripped': strip_bbcode(s),
                    'markdown': md,
                    'html': markdown(md),
                    })

    tmpl = jinja2.Template(
        resource_string(__name__, 'bbcode_test_page.jinja2'),
        autoescape=True,
        undefined=jinja2.StrictUndefined)

    outfp.write(tmpl.render(samples=samples))
