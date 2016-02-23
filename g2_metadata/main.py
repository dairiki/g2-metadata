#! -*- coding: utf-8 -*-
from __future__ import absolute_import

try:
    import cPickle as pickle
except ImportError:
    import pickle

import click
import sqlalchemy as sa

from . import dumper
from . import loader

engine = sa.create_engine('mysql://gallery@furry/gallery2?charset=utf8',
                          echo=False)
Session = sa.orm.sessionmaker(bind=engine)
session = Session()


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
    pass


@main.command()
@click.option('outfp', '--output', '-o', required=True,
              type=click.File('w', encoding='ascii', atomic=True),
              help="Output file (.yml)")
@click.argument('dbsession', type=DBURL, metavar='<dburi>')
def dump(dbsession, outfp):
    dumper.dump_metadata(dbsession, outfp)


@main.command(name='yaml-to-pck')
@click.option('outfp', '--output', '-o', required=True,
              type=click.File('wb', atomic=True),
              help="Output file (.pck)")
@click.argument('infp', type=click.File('r'), metavar='<input.yml>')
def yaml_to_pck(infp, outfp):
    data = loader.load(infp)
    pickle.dump(data, outfp, pickle.HIGHEST_PROTOCOL)
