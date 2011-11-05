#!/bin/sh
#
# This file becomes the post-install section of the generated spec file.
#

# ensure permissions of bin files
chmod 700 /usr/bin/migasfree*

#%update_mime_database
gtk-update-icon-cache --quiet /usr/share/icons/hicolor/
