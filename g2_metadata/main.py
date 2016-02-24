#! -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import sys
try:
    import cPickle as pickle
except ImportError:
    import pickle

import click
import sqlalchemy as sa

from . import dumper
from . import loader
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
@click.argument('infp', type=click.File('r'), default=sys.stdin,
                metavar='[<input.yml>]')
def yaml_to_pck(infp, outfp):
    """ Pickle YAML metadata (for faster loading).
    """
    data = loader.load(infp)
    pickle.dump(data, outfp, pickle.HIGHEST_PROTOCOL)


@main.command(name='to-sigal')
@click.option('--albums', default='albums',
              type=click.Path(exists=True, file_okay=False, writable=True),
              help="Path to albums directory", show_default=True)
@click.argument('infp', type=click.File('rb'), metavar='<metadata.pck>')
def to_sigal(infp, albums):
    """ Write sigal metadata.
    """
    data = pickle.load(infp)
    sigal.write_metadata(data, albums)
