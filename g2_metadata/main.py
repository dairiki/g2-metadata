#! -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import io
import os
import sys
try:
    import cPickle as pickle
except ImportError:
    import pickle

import click
import sqlalchemy as sa

from . import dumper
from . import loader
from . import markup
from . import sigal

engine = sa.create_engine('mysql://gallery@furry/gallery2?charset=utf8',
                          echo=False)
Session = sa.orm.sessionmaker(bind=engine)
session = Session()


log = logging.getLogger(__name__)


class DbUrl(click.ParamType):
    name = 'dburl'

    def convert(self, value, param, ctx):
        engine = sa.create_engine(value,
                                  connect_args={'charset': 'utf8'},
                                  echo=False)
        return sa.orm.Session(bind=engine)

DBURL = DbUrl()


class Metadata(click.Path):
    name = 'metadata'

    def __init__(self):
        super(Metadata, self).__init__(exists=True, dir_okay=False)

    def convert(self, value, param, ctx):
        path = super(Metadata, self).convert(value, param, ctx)
        ext = os.path.splitext(path)[1]
        with io.open(path, 'rb') as fp:
            if ext.lower() == '.pck':
                return pickle.load(fp)
            else:
                return loader.load(fp)

    @staticmethod
    def from_stdin():
        return loader.load(sys.stdin)  # read YAML from STDIN


METADATA = Metadata()


@click.group()
def main():
    # FIXME: control logging level
    logging.basicConfig(level=logging.DEBUG)


@main.command()
@click.option('outfp', '--output', '-o', default=sys.stdout,
              type=click.File('w', encoding='ascii', atomic=True),
              help="Output file (.yml) [default: stdout]")
@click.argument('dbsession', type=DBURL, metavar='<dburi>')
def dump(dbsession, outfp):
    """ Dump gallery2 metadata to YAML.
    """
    dumper.dump_metadata(dbsession, outfp)


@main.command(name='yaml-to-pck')
@click.option('outfp', '--output', '-o', required=True,
              type=click.File('wb', atomic=True),
              help="Output file (.pck)")
@click.argument('metadata', type=METADATA, required=False,
                metavar='[<metadata.yml>]')
def yaml_to_pck(metadata, outfp):
    """ Pickle YAML metadata (for faster loading).
    """
    if metadata is None:
        metadata = METADATA.from_stdin()
    pickle.dump(metadata, outfp, pickle.HIGHEST_PROTOCOL)


@main.command(name='to-sigal')
@click.option('--albums', default='albums',
              type=click.Path(exists=True, file_okay=False, writable=True),
              help="Path to albums directory", show_default=True)
@click.argument('metadata', type=METADATA, required=False,
                metavar='[<metadata.pck>|<metadata.yml>]')
def to_sigal(metadata, albums):
    """ Write sigal metadata.
    """
    if metadata is None:
        metadata = METADATA.from_stdin()
    sigal.write_metadata(metadata, albums)


@main.command(name='bbcode-test')
@click.option('outfp', '--output', '-o', default=sys.stdout,
              type=click.File('w', encoding='utf-8', atomic=True),
              help="Output file (.html) [default: stdout]")
@click.argument('metadata', type=METADATA, required=False,
                metavar='[<metadata.pck>|<metadata.yml>]')
def bbcode_test(metadata, outfp):
    """ Write HTML file with bbcode conversion samples (for testing)
    """
    if metadata is None:
        metadata = METADATA.from_stdin()
    markup.make_bbcode_test_page(metadata, outfp)
