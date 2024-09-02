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
import imaplib
import sys
import urllib
import urllib.parse
from _socket import gaierror

from libs.core.mailParser import mailParser
from libs.kodion.gui_manager import *
from libs.kodion.addon import Addon
from libs.translations import *

class mail2pyload:

    def __init__(self):

        # -- Constants ----------------------------------------------
        self._ADDON_ID = 'plugin.program.mail2pyload'

        width = getScreenWidth()
        addon = Addon(self._ADDON_ID)

        self._NAME = addon.getAddonInfo('name')
        self._FANART = addon.getAddonInfo('fanart')
        self._ICON = addon.getAddonInfo('icon')
        self._NAVART = addon.getAddonInfo('navart')
        self._NEXTPAGE = addon.getAddonInfo('nextpage')
        self._POSTERWIDTH = int(width / 3)
        self._DEFAULT_IMAGE_URL = ''
        self._t = Translations(addon)

        self._IMAP_SERVER = addon.getSetting('imap_server')
        self._IMAP_PORT = int(addon.getSetting('imap_port'))
        self._IMAP_USERNAME = addon.getSetting('imap_username')
        self._IMAP_PASSWORD = addon.getSetting('imap_password')
        self._IMAP_FOLDER = '\"' + addon.getSetting('imap_folder') + '\"'
        self._HOSTER_WHITELIST = addon.getSetting('hoster_whitelist')
        self._HOSTER_BLACKLIST = addon.getSetting('hoster_blacklist')

        self._guiManager = GuiManager(sys.argv[1], self._ADDON_ID, self._DEFAULT_IMAGE_URL, self._FANART)

    def setHomeView(self, **args):
        _args = args

        self._guiManager.addDirectory(title=self._t.getString(NEW_MAIL), poster=self._ICON,
                                      args=self._buildArgs(method='list', param='NEWMAIL'))
        self._guiManager.addDirectory(title=self._t.getString(PYLOAD_PACKAGE), poster=self._ICON,
                                      args=self._buildArgs(method='list', param='PYLOAD_PACKAGE'))


    def setListView(self, **kwargs):
        param = kwargs.get('param')
        page = kwargs.get('page')
        tag = kwargs.get('tag')
        if page is None:
            page = 1

        {
            'NEWMAIL': self.setMailView
        }[param](page=page, tag=tag)


    def setMailView(self, **kwargs):
        page = kwargs.get('page')
        tag = kwargs.get('tag')

        try:

            p =  mailParser(self._IMAP_SERVER, self._IMAP_PORT, self._IMAP_USERNAME, self._IMAP_PASSWORD, self._IMAP_FOLDER, self._HOSTER_WHITELIST, self._HOSTER_BLACKLIST)
            p.getNewMails()

        except gaierror:
            self._guiManager.setToastNotification(self._t.getString(ERROR), self._t.getString(IMAP_SERVER_NOT_REACHABLE))
        except ConnectionRefusedError:
            self._guiManager.setToastNotification(self._t.getString(ERROR), self._t.getString(IMAP_SERVER_REFUSED))
        except imaplib.IMAP4.error as e:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), e.args[0])


    @staticmethod
    def _buildArgs(**kwargs):
        method = kwargs.get('method')
        param = kwargs.get('param')
        page = kwargs.get('page')
        tag = kwargs.get('tag')
        navigation = kwargs.get('navigation')

        args = {
            'method': method
        }

        if param is not None:
            args['param'] = param

        if page is not None:
            args['page'] = page

        if tag is not None:
            args['tag'] = tag

        if navigation is not None:
            args['navigation'] = navigation

        return args

    @staticmethod
    def _get_query_args(s_args):
        args = urllib.parse.parse_qs(urllib.parse.urlparse(s_args).query)

        for key in args:
            args[key] = args[key][0]
        return args

    def run(self):
        args = self._get_query_args(sys.argv[2])

        if args is None or args.__len__() == 0:
            args = self._buildArgs(method='home')

        method = args.get('method')
        param = args.get('param')
        page = args.get('page')
        tag = args.get('tag')
        navigation = args.get('navigation')

        {
            'home': self.setHomeView,
            'list': self.setListView
        }[method](param=param, page=page, tag=tag, navigation=navigation)

        self._guiManager.endOfDirectory()
