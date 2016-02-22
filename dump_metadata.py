#! -*- coding: utf-8 -*-

from datetime import datetime
import re
import sys

import sqlalchemy as sa
import yaml

import models

engine = sa.create_engine('mysql://gallery@furry/gallery2?charset=utf8',
                          echo=False)
Session = sa.orm.sessionmaker(bind=engine)
session = Session()


class Dumper(yaml.Dumper):
    def represent_datetime(self, data):
        # Hack to get datetimes with 'T' separator, and 'Z' zone
        return self.represent_scalar(
            u'tag:yaml.org,2002:timestamp',
            data.replace(microsecond=0).isoformat() + u'Z')

    def represent_unicode(self, data):
        style = None
        if '\n' in data:
            # Translate from DOS to UNIX newline conventions
            lines = re.split('\r?\n', data)
            max_len = max(len(line) for line in lines)
            style = '>' if max_len > 65 else '|'
            data = '\n'.join(lines)
        return self.represent_scalar(u'tag:yaml.org,2002:str', data, style)

    def represent_long(self, data):
        return self.represent_scalar(u'tag:yaml.org,2002:int', unicode(data))

Dumper.add_representer(datetime, Dumper.represent_datetime)
Dumper.add_representer(unicode, Dumper.represent_unicode)
Dumper.add_representer(long, Dumper.represent_long)


class TestDumper(object):
    def dump(self, data):
        dumped = yaml.dump(data, Dumper=Dumper)
        ENDING = '\n...\n'
        assert dumped.endswith(ENDING)
        return dumped[:-len(ENDING)]

    def test_represent_datetime(self):
        dt = datetime(2011, 2, 3, 4, 5, 6, 7)
        assert self.dump(dt) == '2011-02-03T04:05:06Z'

    def test_represent_unicode(self):
        assert self.dump(u'abc') == u'abc'

    def test_represent_long(self):
        assert self.dump(42L) == u'42'


# TODO:
# - Album thumbnail
# - Sidecar format?


def main():
    # Precache all the items in the gallery, so we don't have to query each one
    # individually.
    derivatives = models.Item.derivatives.of_type(
        sa.orm.with_polymorphic(models.Derivative, [models.DerivativeImage],
                                aliased=True))
    cache_items = (
        session.query(models.Item)
        .with_polymorphic([
            models.AlbumItem,
            models.LinkItem,
            models.MovieItem,
            models.PhotoItem,
            ])
        .options(
            sa.orm.subqueryload('parent'),
            sa.orm.subqueryload('link'),
            sa.orm.subqueryload('subitems'),
            sa.orm.subqueryload('comments'),
            #sa.orm.subqueryload(derivatives).joinedload('source'),
            )
        ).all()

    # Find the top-level album for the gallery
    root = session.query(models.AlbumItem).filter_by(parent_id=0).one()
    json = root.__json__(omit=['derivatives'])
    yaml.dump(json, sys.stdout, Dumper,
              width=65,
              default_flow_style=False,
              explicit_start=True)

if __name__ == '__main__':
    main()
