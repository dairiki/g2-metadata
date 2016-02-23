Description
===========

Dump gallery2_ image gallery meta-data to a huge YaML file.


Introduction
============

I have a bunch of photographs in a Gallery photo archive.
(Gallery is an web-based photo archive manager written in PHP.)
The Gallery project has long since been end-of-lifed,
so it is time to get to pictures into some other sort of gallery.

Gallery stores all its image meta-data (other than EXIF data)
in a MySQL database.

This package provides a command-line utility which can be used to
dump most of that meta-data to a (giant) YAML file,
the idea being that once the data is out of MySQL it should be easier to
write a script to massage the meta-data into a format usable by some other
gallery generator (e.g. sigal_.)

.. warning::
   This is throw-away “works for me” code.  Your mileage may vary.


Authors
=======

`Jeff Dairiki`_

.. _gallery2: http://galleryproject.org/
.. _sigal: http://sigal.saimon.org/
.. _Jeff Dairiki: mailto:dairiki@dairiki.org
