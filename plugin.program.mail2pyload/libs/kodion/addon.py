# -*- coding: utf-8 -*-
# Copyright 2024 WebEye
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os

import xbmcaddon
import xbmcvfs
import json


class Addon(xbmcaddon.Addon):

    def __init__(self, id):
        self._id = id
        xbmcaddon.Addon.__init__(self, id)
        self._debug = os.getenv('kodi_debug') is not None

    def getAddonInfo(self, name):
        if name == 'navart':
            return xbmcvfs.translatePath('special://home/addons/' + self._id + '/resources/assets/menu.png')

        if name == 'nextpage':
            return xbmcvfs.translatePath('special://home/addons/' + self._id + '/resources/assets/next.png')

        if not self._debug:
            return xbmcaddon.Addon.getAddonInfo(self, name)
        else:
            if name == 'id':
                return self._id
            elif name == 'name':
                return 'HDTrailers (reloaded)'
            elif name == 'icon':
                return xbmcvfs.translatePath('special://home/addons/' + self._id + '/resources/assets/icon.png')

    def getSetting(self, name):
        if not self._debug:
            return xbmcaddon.Addon.getSetting(self, name)
        else:

            with open('settings.json') as f:
               s = json.load(f)

            return s[name]
