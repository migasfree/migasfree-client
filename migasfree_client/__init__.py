#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2011-2013 Jose Antonio Chavarría
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Author: Jose Antonio Chavarría <jachavar@gmail.com>

__author__ = 'Jose Antonio Chavarría'
__file__ = '__init__.py'
__version__ = '2.1'
__date__ = '2013-01-26'
__license__ = 'GPLv3'

import gettext
import locale
import __builtin__
__builtin__._ = gettext.gettext

# i18n
APP = 'migasfree-client'
gettext.install(APP, '/usr/share/locale', unicode=1)

gettext.bindtextdomain(APP, '/usr/share/locale')
if hasattr(gettext, 'bind_textdomain_codeset'):
    gettext.bind_textdomain_codeset(APP, 'UTF-8')
gettext.textdomain(APP)

locale.bindtextdomain(APP, '/usr/share/locale')
if hasattr(locale, 'bind_textdomain_codeset'):
    locale.bind_textdomain_codeset(APP, 'UTF-8')
locale.textdomain(APP)

# http://fedoraproject.org/wiki/Features/PythonEncodingUsesSystemLocale
# begin unicode hack
import sys

if sys.getdefaultencoding() != 'utf-8':
    try:
        sys.setdefaultencoding('utf-8')
    except AttributeError:
        pass

    import pango
    # now default enconding is 'utf-8' ;)
# end unicode hack
