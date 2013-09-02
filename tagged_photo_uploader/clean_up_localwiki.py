#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This script should be run on the server to wipe out everything from the
tests."""

from pages.models import PageFile, Page

# Delete any blank pages cause by the api bug
# https://github.com/localwiki/localwiki/issues/616
try:
    page = PageFile.objects.get(name='')
except PageFile.DoesNotExist:
    pass
else:
    for version in page.versions.all():
        version.delete()
    page.delete(track_changes=False)

# Delete all existence of the three test pages.
test_page_names = ['Existing Upload Test Page',
                   'Non Existing Upload Test Page',
                   'This Page Does Not Exist']
for page_name in test_page_names:
    try:
        page = Page.objects.get(name=page_name)
    except Page.DoesNotExist:
        pass
    else:
        for version in page.versions.all():
            version.delete()
        page.delete(track_changes=False)

# TODO : This still isn't wiping the page history instance. I need to figure
# out how to do that.
