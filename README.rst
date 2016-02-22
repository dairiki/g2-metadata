Description
===========

Dump gallery2_ image gallery metadata


Introduction
============

I have a bunch of photographs in a Gallery photo archive.
(Gallery is an web-based photo archive manager written in PHP.)
The Gallery project has long since been end-of-lifed,
so it is time to get to pictures into some other sort of gallery.

Gallery stores all its image metadata (other than EXIF data)
in a MySQL database.

This package provides a command-line utility which can be used to
dump most of that metadata to a (giant) YAML file.


Authors
=======

`Jeff Dairiki`_

.. _gallery2: http://galleryproject.org/

.. _Jeff Dairiki: mailto:dairiki@dairiki.org
