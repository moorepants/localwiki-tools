This script allows you to upload photos with specific tags to a LocalWiki using
the LocalWiki API. It is a nice way to build stub pages based on photos that
you take and then tag. If the page exists, then the photo is uploaded and
associated with the page, and embedded in the page. If the page doesn't exist,
then it is created before doing the above. If the photo has a caption it will
be added to the embedded image as the caption. The photos will be autorotated
before upload if they have the correct Exif orientation information.

Installation
============

To run the script just make sure you have the requirements:

- slumber
- GExiv2
- jhead
- nose (for tests only)

To install on Ubuntu 13.04:

First install GExiv2 to your system::

   $ sudo aptitude install build-essential libexiv2-dev libtool libgirepository1.0-dev m4
   $ git clone git://git.yorba.org/gexiv2
   $ cd gexiv2
   $ ./configure --enable-introspection
   $ make
   $ sudo make install

Get jhead::

   $ sudo aptitude install jhead

Make a virtual environment (using virtualenvwrapper)::

   $ mkvirtualenv mywiki

Get slumber::

   (mywiki)$ pip install slumber pyyaml simplejson

Get nose::

   (mywiki)$ pip install nose

I run GExiv2 in a virtual environment using this hack:

http://stackoverflow.com/questions/17472124/how-to-install-gexiv2-on-a-virtualenv

Usage
=====

First pick a tagging schema. You will need a main tag to identify photos that
belong on your localwiki and also a tag to identify which page they should be
associated with. For example, I open my photos in Shotwell and tag every photo
that I want to upload with ``cleveland wiki``. Then I go through each of those
photos and add a tag in the form ``page:<exact page name>`` to specify the page
to associated the image with. For example the second tag could be ``page:Front
Page`` if I want the image to be added to the page named ``Front Page``. The main
tag can be anything you like and the page tag must have some kind of prefix, in
this case it was ``page:`` (the script assumes ``page:`` as the default prefix.

Once you have some tagged photos in some arbitrary directories, you can upload
them using either the command line or through the Python API.

Command Line
------------

You can use the script through the command line. Simply call the script with
Python and supply it with all of the directories that you'd like to search for
files with appropriate tags (this is not a recursive search)::

   $ python upload_tagged_photos.py <directories>

For example if I have photos in in two directories ``~/Pictures/2013-08-27`` and
``~/Pictures/2013-08-26`` that I would like to upload then use::

   $ python upload_tagged_photos.py ~/Pictures/2013-08-27 ~/Pictures/2013-08-26

If all you supply are the directories then you must have a ``test.cfg`` file in
the same directory as ``upload_tagged_photos.py`` with this as its contents::

   [localwiki]
   api_url=http://<yourlocalwiki>.org/api/
   user_name=<your username>
   api_key=<your api key>
   main_keyword=<your main tag/keyword>
   page_keyword_prefix=<your page tag/keyword prefix>

The things in carets should of course be replaced by values that are useful to
you. And don't forget the trailing slash on the url.

You can also pass these in via the command line if you don't want to use the
``test.cfg`` file (you must pass at least the main tag/keyword and the api url)::

   $ python upload_tagged_photos.py --url http://<yourlocalwiki>.org/api/ --keyword <your main tag/keyword> <directories>

Afterwards, you will be prompted for an user name and api key with the previous
command, but can also pass them in with::

   $ python upload_tagged_photos.py --url http://<yourlocalwiki>.org/api/ --keyword <your main tag/keyword> --username <your user name> --apikey <your api key> <directories>

Python API
----------

The same thing can be accomplished in the Python interpreter or a Python
program::

   $ python
   >>> from upload_tagged_photos import ImageUploader
   >>> uploader = ImageUploader(<your api url>, username=<your user name>, api_key=<your api key>)
   >>> uploader.upload(<your main keyword>, <path to dir1>, <path to dir2>, page_keyword_prefix=<your page keyword prefix>)

Tests
=====

**Warning: With the latest localwiki, 0.5.4, these tests will likely break your
recent changes page. It introduces a page with a blank slug and blank name,
that will have to be deleted through the localwiki shell afterwards.**

The tests rely on a ``test.cfg`` file being in the directory. To run them with
nose type::

   $ nosetests

TODO
====

- Create a map point if the photo has a geo tag.
- Resize images to a more reasonable size instead of the huge size that comes
  off cameras.
- Add instructions for deleting the page with no name.
- When pages are created, tag them as stub and put a stub banner at the top so
  we know they need more info.
- Add tests for the image rotation method.
