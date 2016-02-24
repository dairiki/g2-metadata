# -*- coding: utf-8 -*-
""" Code for fixing screwed up EXIF Orientation tags.
"""
from __future__ import absolute_import

import logging
import piexif

log = logging.getLogger(__name__)


def _exif_property(ifd, tag):
    def fget(self):
        try:
            return self.exif[ifd][tag]
        except KeyError:
            return None

    def fset(self, value):
        self.exif[ifd][tag] = value
        self._update()

    return property(fget, fset)


class Exif(object):
    def __init__(self, filename):
        self.filename = filename
        self.exif = piexif.load(filename)

    def _update(self):
        packed = piexif.dump(self.exif)
        piexif.insert(packed, self.filename)

    pixel_x_dimension = _exif_property('Exif', piexif.ExifIFD.PixelXDimension)
    pixel_y_dimension = _exif_property('Exif', piexif.ExifIFD.PixelYDimension)
    orientation = _exif_property('0th', piexif.ImageIFD.Orientation)


def looks_borked(exif):
    orientation = exif.orientation
    width = exif.pixel_x_dimension
    height = exif.pixel_y_dimension

    if orientation is None or width is None or height is None:
        return None         # no exif data to check
    elif orientation in (5, 6, 7, 8):
        # If image is taller than wide, it looks like the specified
        # rotation has already been applied.  (We're borked.)
        return width < height
    elif orientation == 1:
        return False
    else:
        return None         # don't know how to check other orientations


def fix_exif(filename):
    exif = Exif(filename)
    if looks_borked(exif):
        log.info("%s: setting EXIF orientation to 1", filename)
        exif.orientation = 1
