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
import base64
import imaplib
import json
import sys
import urllib
import urllib.parse


import requests
from _socket import gaierror

from libs.core.mailParser import mailParser
from libs.core.pyloadAPI import pyloadAPI
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

        self._PYLOAD_SERVER = addon.getSetting('pyload_server')
        self._PYLOAD_PORT = int(addon.getSetting('pyload_port'))
        self._PYLOAD_USERNAME = addon.getSetting('pyload_username')
        self._PYLOAD_PASSWORD = addon.getSetting('pyload_password')

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
            'NEWMAIL': self.setMailView,
            'MAILDETAIL': self.setMailDetailView,
            'PYLOAD_PACKAGE': self.setPyLoadPackageView,
            'PYLOAD_QUEUE': self.setPyLoadPackageDetailView,
            'PYLOAD_COLLECTOR': self.setPyLoadPackageDetailView,
            'PYLOAD_PACKAGE_DETAIL': self.setPyloadPackageContentView
        }[param](page=page, tag=tag, param=param)

    def setMailDetailView(self, **kwargs):
        page = kwargs.get('page')
        tag = kwargs.get('tag')

        if not tag is None:
            tag = self._base64Decode(tag)
            mail = json.loads(tag)

            poster = None
            if len(mail['images']) > 0:
                poster = mail['images'][0]



            for i in mail['images']:

                tag = self._base64Encode(i)
                url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(self._buildArgs(method='show', param='IMAGE', tag=tag))
                self._guiManager.addItem(title='[THUMB] ' + mail['subject'],url=url,poster=i)

            for p in mail['packages']:
                url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                    self._buildArgs(method='show', param='PACKAGE_ITEM'))
                self._guiManager.addItem(title=p['subject'], url=url, poster=poster)



            # print(mail['subject'])
            # print(mail['description'])
            # for i in mail['images']:
            #     print(i)
            #
            # for p in mail['packages']:
            #     print(p['subject'])
            #     for h in p['hosters']:
            #         print(h['subject'] + ": " + h['link'])
            #
            # print('________________________________________')


    def setPyLoadPackageView(self, **kwargs):

        self._guiManager.addDirectory(title=self._t.getString(PYLOAD_QUEUE), poster=self._ICON,
                                      args=self._buildArgs(method='list', param='PYLOAD_QUEUE'))
        self._guiManager.addDirectory(title=self._t.getString(PYLOAD_COLLECTOR), poster=self._ICON,
                                      args=self._buildArgs(method='list', param='PYLOAD_COLLECTOR'))


    def setPyLoadPackageDetailView(self, **kwargs):
        param = kwargs.get('param')

        try:

            api = pyloadAPI(self._PYLOAD_SERVER, self._PYLOAD_PORT, self._PYLOAD_USERNAME, self._PYLOAD_PASSWORD)
            response = None
            if param == 'PYLOAD_QUEUE':
                response = api.getQueue()
            elif param == 'PYLOAD_COLLECTOR':
                response = api.getCollector()

            if not response is None and response.status_code == 200:
                if response.text:
                    data = json.loads(response.text)
                    for item in data:
                        name = item['name']
                        if item['sizedone'] > 0 and item['sizetotal'] > 0:
                            pct = item['sizedone'] / item['sizetotal'] * 100
                            name = f'[{pct}%] {name}'

                        self._guiManager.addDirectory(title=name, poster=self._ICON,
                                                      args=self._buildArgs(method='list', param='PYLOAD_PACKAGE_DETAIL'))

            else:
                self.handlePyLoadErrorResponse(response)

        except requests.exceptions.ConnectionError as e:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(SERVER_NOT_REACHABLE))


    def setPyloadPackageContentView(self):
        pass

    def setMailView(self, **kwargs):
        page = kwargs.get('page')
        tag = kwargs.get('tag')

        try:

            p =  mailParser(self._IMAP_SERVER, self._IMAP_PORT, self._IMAP_USERNAME, self._IMAP_PASSWORD, self._IMAP_FOLDER, self._HOSTER_WHITELIST, self._HOSTER_BLACKLIST)
            mails = p.getNewMails()
            for mail in mails:
                poster = self._ICON
                if len(mail['images']) > 0:
                    poster=mail['images'][0]

                infoLabels = {
                    'Title': mail['subject'],
                    'Plot': mail['description']
                }

                tag = json.dumps(mail)
                tag = self._base64Encode(tag)

                seen_url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                    self._buildArgs(method='markmail', param='SEEN', tag=mail['uid']))
                done_url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                    self._buildArgs(method='markmail', param='DONE', tag=mail['uid']))
                deleted_url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                    self._buildArgs(method='markmail', param='DELETED', tag=mail['uid']))

                contextmenu = [
                    (self._t.getString(MARK_MAIL_SEEN), f'RunPlugin("{seen_url}")'),
                    (self._t.getString(MARK_MAIL_DONE), f'RunPlugin("{done_url}")'),
                    (self._t.getString(MARK_MAIL_DELETED), f'RunPlugin("{deleted_url}")'),
                ]

                self._guiManager.addDirectory(title=mail['subject'], poster=poster, infoLabels=infoLabels, _type='video',
                                              contextmenu=contextmenu,
                                              args=self._buildArgs(method='list', param='MAILDETAIL', tag=tag))

        except gaierror:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), self._t.getString(SERVER_NOT_REACHABLE))
        except ConnectionRefusedError:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), self._t.getString(SERVER_REFUSED))
        except imaplib.IMAP4.error as e:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), e.args[0])


    def showEntity(self, **kwargs):
        param = kwargs.get('param')
        tag = kwargs.get('tag')

        {
            'IMAGE':            self.showImage,
            'PACKAGE_ITEM':     self.showImage
        }[param](tag=tag)


    def showImage(self, **kwargs):
        try:
            tag = kwargs.get('tag')
            if tag:
                image = self._base64Decode(tag)

                xbmc.executebuiltin('ShowPicture(%s)' % image)

        except AttributeError:
            pass

    def markMail(self, **kwargs):
        param = kwargs.get('param')
        tag = kwargs.get('tag')

        try:

            p = mailParser(self._IMAP_SERVER, self._IMAP_PORT, self._IMAP_USERNAME, self._IMAP_PASSWORD, self._IMAP_FOLDER,
                           self._HOSTER_WHITELIST, self._HOSTER_BLACKLIST)

            p.setFlag(tag, param, True)
            if param != 'SEEN':
                xbmc.executebuiltin('Container.Refresh')


        except gaierror:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), self._t.getString(SERVER_NOT_REACHABLE))
        except ConnectionRefusedError:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), self._t.getString(SERVER_REFUSED))
        except imaplib.IMAP4.error as e:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), e.args[0])

    def handlePyLoadErrorResponse(self, response):
        if not response is None:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(PYLOAD_STATUS_CODE) + f' ({response.status_code}) {response.reason}')

        else:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(PYLOAD_ERROR_UMNKOWN))

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
    def _base64Encode(s):
        b = s.encode("ascii")

        encoded = base64.b64encode(b)
        return encoded.decode("ascii")


    @staticmethod
    def _base64Decode(s):
        b = s.encode("ascii")
        decoded = base64.b64decode(b)
        return decoded.decode("ascii")

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
            'home':         self.setHomeView,
            'list':         self.setListView,
            'show':         self.showEntity,
            'markmail':     self.markMail
        }[method](param=param, page=page, tag=tag, navigation=navigation)

        self._guiManager.endOfDirectory()
