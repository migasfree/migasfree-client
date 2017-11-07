#!/bin/sh
#
# This file becomes the post-uninstall section of the generated spec file.
#

#%clean_mime_database
gtk-update-icon-cache --quiet /usr/share/icons/hicolor/ || :
