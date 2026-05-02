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

import binascii
import imaplib
import json
import sys
import urllib
import urllib.parse
import re


import requests
from _socket import gaierror

import xbmc
from libs.common.tools import base64Decode, base64Encode, formatSize, get_query_args, \
    doLinkMatch, compileRegExPattern, get_rddomain, replace_domain, loads_dict
from libs.core.mailParser import mailParser
from libs.core.pyloadAPI import pyloadAPI
from libs.core.realDebritCore import realdebritCore
from libs.kodion.gui_manager import *
from libs.kodion.addon import Addon
from libs.translations import *
from libs.core.databaseCore import databaseCore

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

        self._ERROR_ICON = f'special://home/addons/{self._ADDON_ID}/resources/assets/icon-error.jpg'
        self._OK_ICON = f'special://home/addons/{self._ADDON_ID}/resources/assets/icon-ok.jpg'

        self._IMAP_SERVER = addon.getSetting('imap_server')
        self._IMAP_PORT = int(addon.getSetting('imap_port'))
        self._IMAP_USERNAME = addon.getSetting('imap_username')
        self._IMAP_PASSWORD = addon.getSetting('imap_password')
        self._IMAP_FOLDER = '\"' + addon.getSetting('imap_folder') + '\"'

        _HOSTER_WHITELIST = addon.getSetting('hoster_whitelist')
        self._HOSTER_WHITELIST_COMPILED = None
        if _HOSTER_WHITELIST and _HOSTER_WHITELIST != "":
            self._HOSTER_WHITELIST_COMPILED = re.compile(_HOSTER_WHITELIST, re.IGNORECASE)

        _HOSTER_BLACKLIST = addon.getSetting('hoster_blacklist')
        self._HOSTER_BLACKLIST_COMPILED = None
        if _HOSTER_BLACKLIST and _HOSTER_BLACKLIST != "":
            self._HOSTER_BLACKLIST_COMPILED = re.compile(_HOSTER_BLACKLIST, re.IGNORECASE)

        self._RD_DOMAINS_COMPILED = None

        self._PYLOAD_SERVER = addon.getSetting('pyload_server')
        self._PYLOAD_PORT = int(addon.getSetting('pyload_port'))
        self._PYLOAD_USERNAME = addon.getSetting('pyload_username')
        self._PYLOAD_PASSWORD = addon.getSetting('pyload_password')

        self._DATABASE_HOST = addon.getSetting('database_host')
        self._DATABASE_PORT = int(addon.getSetting('database_port'))
        self._DATABASE_USER = addon.getSetting('database_user')
        self._DATABASE_PASSWORD = addon.getSetting('database_password')
        self._DATABASE_NAME = addon.getSetting('database_name')

        self._REALDEBRIT_TOKEN = addon.getSetting('realdebrit_token')

        self._api = pyloadAPI(self._PYLOAD_SERVER, self._PYLOAD_PORT, self._PYLOAD_USERNAME, self._PYLOAD_PASSWORD)

        self._db = None
        try:
            self._db = databaseCore(host=self._DATABASE_HOST, port=self._DATABASE_PORT, user=self._DATABASE_USER,
                                    password=self._DATABASE_PASSWORD, database=self._DATABASE_NAME)
        finally:
            pass

        self._rdAPI = None
        if self._REALDEBRIT_TOKEN:
            self._rdAPI = realdebritCore(self._REALDEBRIT_TOKEN)

        self._PYLOAD_DEFAULT_PACKAGE_NAME = addon.getSetting('pyload_default_package_name')

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
            tag = base64Decode(tag)
            mail = json.loads(tag)

            poster = None
            if len(mail['images']) > 0:
                poster = mail['images'][0]

            for i in mail['images']:

                tag = base64Encode(i)
                url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(self._buildArgs(method='show', param='IMAGE', tag=tag))
                self._guiManager.addItem(title='[THUMB] ' + mail['subject'],url=url,poster=i)

            for p in mail['packages']:
                url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                    self._buildArgs(method='show', param='PACKAGE_ITEM'))

                contextmenu = []

                for h in p['hosters']:
                    tag = base64Encode( h['link'])

                    pyload_url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                        self._buildArgs(method='add', param='PYLOAD_PACKAGE', tag=tag))

                    contextmenu.append((h['subject'], f'RunPlugin("{pyload_url}")'))

                self._guiManager.addItem(title=p['subject'], url=url, poster=poster, contextmenu=contextmenu)


    def setPyLoadPackageView(self, **kwargs):

        restart_failed_url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
            self._buildArgs(method='restart', param='PYLOAD_FAILED'))

        contextmenu = [
            (self._t.getString(PYLOAD_RESTART_FAILED), f'RunPlugin("{restart_failed_url}")'),
        ]

        self._guiManager.addDirectory(title=self._t.getString(PYLOAD_QUEUE), poster=self._ICON,
                                      contextmenu=contextmenu,
                                      args=self._buildArgs(method='list', param='PYLOAD_QUEUE'))
        self._guiManager.addDirectory(title=self._t.getString(PYLOAD_COLLECTOR), poster=self._ICON,
                                      args=self._buildArgs(method='list', param='PYLOAD_COLLECTOR'))


    def setPyLoadPackageDetailView(self, **kwargs):
        param = kwargs.get('param')

        try:

            response = None
            if param == 'PYLOAD_QUEUE':
                response = self._api.getQueue()
            elif param == 'PYLOAD_COLLECTOR':
                response = self._api.getCollector()

            if not response is None and response.status_code == 200:
                if response.text:
                    data = json.loads(response.text)
                    for item in data:
                        name = item['name']
                        pct = 0

                        done_filesize = item['sizedone']
                        total_filesize = item['sizetotal']
                        if total_filesize > 0:
                            if done_filesize == total_filesize and item['linksdone'] == item['linkstotal']:
                                pct = 100
                            else:
                                if item['linksdone'] == 0:
                                    if done_filesize > 0 and total_filesize > 0:
                                        pct = int(done_filesize / total_filesize * 100)

                                else:
                                    avg_filesize = done_filesize /  item['linksdone']
                                    tmp_total_filesize = avg_filesize * item['linkstotal']
                                    if tmp_total_filesize > total_filesize:
                                        total_filesize = tmp_total_filesize
                                    if total_filesize > 0:
                                        pct = int(done_filesize / total_filesize * 100)

                        if pct > 0:
                            padding = ''
                            if pct < 10:
                                padding = '  '
                            elif pct < 100:
                                padding = ' '

                            name = f'{padding}[{pct}%] {name}'


                        arg = 'PYLOAD_QUEUE'
                        contextTitle = PYLOAD_MOVETO_QUEUE
                        if param == 'PYLOAD_QUEUE':
                            arg = 'PYLOAD_COLLECTOR'
                            contextTitle = PYLOAD_MOVETO_COLLECTOR

                        move_url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                            self._buildArgs(method='move', param=arg, tag=item['pid']))

                        delete_url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                            self._buildArgs(method='delete', param='PYLOAD_PACKAGE', tag=item['pid']))

                        contextmenu = [
                            (self._t.getString(contextTitle), f'RunPlugin("{move_url}")'),
                            (self._t.getString(PYLOAD_DELETE_PACKAGE), f'RunPlugin("{delete_url}")'),
                        ]

                        plot = (f"[B]Link Count[/B]: {item['linksdone']} / {item['linkstotal']}\n"
                                f"[B]Size[/B]: {formatSize(done_filesize)} / {formatSize(total_filesize)}")



                        infoLabels = {
                            'Title': name,
                            'Plot': plot
                        }

                        self._guiManager.addDirectory(title=name, poster=self._ICON, _type='video', infoLabels=infoLabels,
                                                      contextmenu=contextmenu,
                                                      args=self._buildArgs(method='list', param='PYLOAD_PACKAGE_DETAIL',
                                                                           tag=item['pid']))

            else:
                self.handlePyLoadErrorResponse(response)

        except requests.exceptions.ConnectionError as e:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(SERVER_NOT_REACHABLE),icon=self._ERROR_ICON)


    def setPyloadPackageContentView(self, **kwargs):
        param = kwargs.get('param')
        pid = kwargs.get('tag')

        try:
            response = self._api.getPackageData(pid)
            if not response is None and response.status_code == 200:
                if response.text:
                    data = json.loads(response.text)
                    if 'links' in data:
                        for item in data['links']:
                            name = item['name']
                            fid = item['fid']
                            size = item['format_size']
                            plugin = item['plugin']
                            status = item['statusmsg']
                            error = item['error']

                            if error != '':
                                plot = f'[B]Name[/B]: {name}\n[B]Status[/B]: {status}\n[B]Size[/B]: {size}\n[B]Plugin[/B]: {plugin}\n[B]Error[/B]: {error}'
                            else:
                                plot = f'[B]Name[/B]: {name}\n[B]Status[/B]: {status}\n[B]Size[/B]: {size}\n[B]Plugin[/B]: {plugin}'

                            infoLabels = {
                                'Title': name,
                                'Plot': plot
                            }

                            restart_url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                                self._buildArgs(method='restart', param='PYLOAD_FILE', tag=fid))

                            delete_url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                                self._buildArgs(method='delete', param='PYLOAD_FILE', tag=fid))

                            contextmenu = [
                                (self._t.getString(PYLOAD_RESTART_FILE), f'RunPlugin("{restart_url}")'),
                                (self._t.getString(PYLOAD_DELETE_FILE), f'RunPlugin("{delete_url}")'),
                            ]

                            self._guiManager.addDirectory(title=name, poster=self._ICON, _type='video', infoLabels=infoLabels,
                                                          contextmenu=contextmenu,
                                                          args=self._buildArgs()
                                                          )

        except requests.exceptions.ConnectionError as e:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(SERVER_NOT_REACHABLE),icon=self._ERROR_ICON)


    def setMailView(self, **kwargs):
        page = kwargs.get('page')
        tag = kwargs.get('tag')

        try:

            rd_hosterDict = {}
            if self._db:
                rd_hosterlist = self._db.getrealdebritHosts()
                rd_hosterDict = loads_dict(rd_hosterlist)
                self._getRDDomains()

            p =  mailParser(self._IMAP_SERVER, self._IMAP_PORT, self._IMAP_USERNAME, self._IMAP_PASSWORD,
                            self._IMAP_FOLDER, self._HOSTER_WHITELIST_COMPILED, self._HOSTER_BLACKLIST_COMPILED,
                            rd_hosterDict, self._RD_DOMAINS_COMPILED)

            mails = p.getNewMails()

            mails_tag = json.dumps(mails)
            mails_tag = base64Encode(mails_tag)

            for mail in mails:
                poster = self._ICON
                if len(mail['images']) > 0:
                    poster=mail['images'][0]

                package_count = 0
                if 'packages' in mail:
                    package_count = len(mail['packages'])

                infoLabels = {
                    'Title': mail['subject'],
                    'Plot': f'[B]Package Count[/B]: {package_count}\n' + mail['description']
                }

                if package_count > 1:
                    infoLabels['Plot'] = f'[COLOR red][B]Package Count[/B]: {package_count}[/COLOR]\n' + mail['description']

                tag = json.dumps(mail)
                tag = base64Encode(tag)

                deleted_url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                    self._buildArgs(method='markmail', param='DELETED', tag=mail['uid']))

                add_url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                    self._buildArgs(method='addall', param=None, tag=mails_tag))

                delete_all_url = 'plugin://' + self._ADDON_ID + '/?' + urllib.parse.urlencode(
                    self._buildArgs(method='deleteall', param=None, tag=mails_tag))


                contextmenu = [
                    (self._t.getString(PYLOAD_ADDALLTO_PACKAGE), f'RunPlugin("{add_url}")'),
                    (self._t.getString(MARK_MAIL_DELETED), f'RunPlugin("{deleted_url}")'),
                    (self._t.getString(MARK_ALLMAIL_DELETED), f'RunPlugin("{delete_all_url}")'),
                ]

                self._guiManager.addDirectory(title=mail['subject'], poster=poster, infoLabels=infoLabels, _type='video',
                                              contextmenu=contextmenu,
                                              args=self._buildArgs(method='list', param='MAILDETAIL', tag=tag))

        except gaierror:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), self._t.getString(SERVER_NOT_REACHABLE),icon=self._ERROR_ICON)
        except ConnectionRefusedError:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), self._t.getString(SERVER_REFUSED),icon=self._ERROR_ICON)
        except imaplib.IMAP4.error as e:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), e.args[0],icon=self._ERROR_ICON)

    def _getPreferredHosterLink(self, candidates, rd_hosterDict):
        if self._HOSTER_WHITELIST_COMPILED:
            for candidate in candidates:
                if self._HOSTER_WHITELIST_COMPILED.search(candidate):
                    return candidate

        links = []
        if len(rd_hosterDict) > 0:
            for candidate in candidates:
                for hoster in rd_hosterDict:
                    patterns = hoster[1].get('compiledRegExPattern', [])
                    if patterns:
                        if doLinkMatch(patterns, candidate):
                            traffic = hoster[1].get('traffic')
                            if not traffic:
                                return candidate
                            else:
                                links.append({ "candidate": candidate, "trafficLeft": traffic.get('left') })

        if len(links) > 0:
            best = max(links, key=lambda item: item["trafficLeft"])
            if best:
                return best["candidate"]

        return None

    def addMails(self, **kwargs):
        param = kwargs.get('param')
        tag = kwargs.get('tag')

        xbmc.log("populate hosterDict.Begin")
        rd_hosterDict = {}
        if self._db:
            rd_hosterlist = self._db.getrealdebritHosts()
            if rd_hosterlist:
                try:
                    rd_hosterDict = json.loads(rd_hosterlist)
                    xbmc.log("compileRegExPattern.Begin")
                    rd_hosterDict = compileRegExPattern(rd_hosterDict)
                    xbmc.log("compileRegExPattern.End")
                    rd_hosterDict = sorted(
                        rd_hosterDict.items(),
                        key=lambda item: (
                            item[1].get("traffic") is not None,
                            item[1].get("traffic", {}).get("left") is None,
                            -(item[1].get("traffic", {}).get("left") or 0)
                        )
                    )
                finally:
                    pass
        xbmc.log("populate hosterDict.End")

        if tag:
            mails = base64Decode(tag)
            mails = json.loads(mails)
            errorOccurs = False

            for mail in mails:
                if 'packages' in mail:
                    for package in mail['packages']:
                        if 'hosters' in package:
                            candidates =[]
                            for hoster in package['hosters']:
                                if 'link' in hoster:
                                    candidates.append(hoster['link'])

                            xbmc.log("_getPreferredHosterLink.Begin")
                            link = self._getPreferredHosterLink(candidates, rd_hosterDict)
                            xbmc.log("_getPreferredHosterLink.End")
                            if link:
                                self.addEntity(param='PYLOAD_PACKAGE', tag=link)
                            else:
                                errorOccurs = True
                                self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                                      self._t.getString(PYLOAD_ERROR_UNKOWN),
                                                                      icon=self._ERROR_ICON)

            if not errorOccurs:
                self.deleteMails(param=param, tag=tag)

    def deleteMails(self, **kwargs):
        param = kwargs.get('param')
        tag = kwargs.get('tag')

        doit = tag and self._guiManager.MsgBoxYesNo(heading=self._t.getString(PYLOAD_QUESTION),
                                            message=self._t.getString(PYLOAD_DELETE_ALL_MAILS_CONFIRMATION))

        if doit:
            mails = base64Decode(tag)
            mails = json.loads(mails)

            for mail in mails:
                uid = mail.get('uid')
                if uid:
                    self.markMail(param = 'DELETED', tag = str(uid))



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
                image = base64Decode(tag)

                xbmc.executebuiltin('ShowPicture(%s)' % image)

        except AttributeError:
            pass

    def markMail(self, **kwargs):
        param = kwargs.get('param')
        tag = kwargs.get('tag')

        try:

            p = mailParser(self._IMAP_SERVER, self._IMAP_PORT, self._IMAP_USERNAME, self._IMAP_PASSWORD, self._IMAP_FOLDER,
                           self._HOSTER_WHITELIST_COMPILED, self._HOSTER_BLACKLIST_COMPILED, None, None)

            p.setFlag(tag, param, True)
            if param != 'SEEN':
                xbmc.executebuiltin('Container.Refresh')


        except gaierror:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), self._t.getString(SERVER_NOT_REACHABLE),icon=self._ERROR_ICON)
        except ConnectionRefusedError:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), self._t.getString(SERVER_REFUSED),icon=self._ERROR_ICON)
        except imaplib.IMAP4.error as e:
            self._guiManager.setToastNotification(self._t.getString(IMAP_ERROR), e.args[0],icon=self._ERROR_ICON)

    def _getDownloadLink(self, link):
        self._getRDDomains()
        _domain = get_rddomain(link, self._RD_DOMAINS_COMPILED)
        link = replace_domain(link, _domain)

        if self._HOSTER_WHITELIST_COMPILED:
            if self._HOSTER_WHITELIST_COMPILED.search(link):
                return link

        if self._rdAPI:

            rsp = self._rdAPI.unrestrictLink(link)
            if rsp:
                return rsp['download']


        return None

    def _getRDDomains(self):
        if self._db and not self._RD_DOMAINS_COMPILED:
            domains = self._db.getrealdebritDomains()
            domainsDict = loads_dict(domains)
            if domainsDict:
                self._RD_DOMAINS_COMPILED = {
                    key: [re.compile(p, re.IGNORECASE) for p in patterns]
                    for key, patterns in domainsDict.items()
                }

    def addEntity(self, **kwargs):
        param = kwargs.get('param')
        tag = kwargs.get('tag')

        {
            'PYLOAD_PACKAGE': self.addPyLoadPackage
        }[param](tag=tag)

    def addPyLoadPackage(self, tag):
        try:
            tag = base64Decode(tag)
        except UnicodeDecodeError as e:
            pass

        except binascii.Error as e1:
            pass

        link = self._getDownloadLink(tag)
        if link is None:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(PYLOAD_ERROR_CONVERTLINK), icon=self._ERROR_ICON)
            return

        try:
            response = self._api.getCollector()
            pid = 0

            if not response is None and response.status_code == 200:
                if response.text:
                    data = json.loads(response.text)
                    result = next(filter(lambda x: x['name'] == self._PYLOAD_DEFAULT_PACKAGE_NAME , data), None)
                    if not result is None:
                        pid = result['pid']

            else:
                self.handlePyLoadErrorResponse(response)

            if pid == 0:
                response = self._api.addPackage(self._PYLOAD_DEFAULT_PACKAGE_NAME, link)
            else:
                response = self._api.addFiles(pid, link)

            if not response is None and response.status_code == 200:
                self._guiManager.setToastNotification(self._t.getString(PYLOAD_NOTIFICATION), self._t.getString(PYLOAD_ADDED_SUCCESFULLY),icon=self._OK_ICON)
            else:
                self.handlePyLoadErrorResponse(response)

        except requests.exceptions.ConnectionError as e:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR), self._t.getString(SERVER_NOT_REACHABLE),icon=self._ERROR_ICON)

    def moveEntity(self, **kwargs):
        param = kwargs.get('param')
        tag = kwargs.get('tag')

        {
            'PYLOAD_QUEUE': self.movePyloadPackage,
            'PYLOAD_COLLECTOR': self.movePyloadPackage
        }[param](param=param, tag=tag)

    def deleteEntity(self, **kwargs):
        param = kwargs.get('param')
        tag = kwargs.get('tag')

        {
            'PYLOAD_PACKAGE': self.deletePyloadPackage,
            'PYLOAD_FILE': self.deletePyloadFile
        }[param](tag=tag)

    def restartEntity(self, **kwargs):
        param = kwargs.get('param')
        tag = kwargs.get('tag')

        {
            'PYLOAD_PACKAGE': self.restartPyloadPackage,
            'PYLOAD_FILE': self.restartPyloadFile,
            'PYLOAD_FAILED': self.restartPyloadFailed,
        }[param](tag=tag)

    def movePyloadPackage(self, **kwargs):
        param = kwargs.get('param')
        pid = kwargs.get('tag')

        dest = {
            'PYLOAD_QUEUE': 1,
            'PYLOAD_COLLECTOR': 0
        }[param]

        try:

            response = self._api.movePackage(pid=pid, destination=dest)

            if not response is None and response.status_code == 200:
                self._guiManager.setToastNotification(self._t.getString(PYLOAD_NOTIFICATION),
                                                      self._t.getString(PYLOAD_MOVED_SUCCESFULLY), icon=self._OK_ICON)

                xbmc.executebuiltin('Container.Refresh')
            else:
                self.handlePyLoadErrorResponse(response)



        except requests.exceptions.ConnectionError as e:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(SERVER_NOT_REACHABLE),icon=self._ERROR_ICON)


    def deletePyloadPackage(self, **kwargs):
        pid = kwargs.get('tag')

        try:
            response = self._api.getPackageInfo(pid=pid)
            if not response is None and response.status_code == 200:

                doit = True
                data = json.loads(response.text)

                sizetotal = 0
                sizedone = 0
                if not data['sizetotal'] is None:
                    sizetotal = data['sizetotal']

                if not data['sizedone'] is None:
                    sizedone = data['sizedone']

                if sizetotal == 0 or (sizetotal > 0 and sizedone < sizetotal):
                    doit = self._guiManager.MsgBoxYesNo(heading=self._t.getString(PYLOAD_QUESTION), message=self._t.getString(PYLOAD_DELETE_CONFIRMATION))

                if doit:
                    response = self._api.deletePackage(pid=pid)

                    if not response is None and response.status_code == 200:
                        self._guiManager.setToastNotification(self._t.getString(PYLOAD_NOTIFICATION),
                                                              self._t.getString(PYLOAD_DELETED_SUCCESFULLY), icon=self._OK_ICON)

                        xbmc.executebuiltin('Container.Refresh')

                    else:
                        self.handlePyLoadErrorResponse(response)

            else:
                self.handlePyLoadErrorResponse(response)

        except requests.exceptions.ConnectionError as e:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(SERVER_NOT_REACHABLE),icon=self._ERROR_ICON)

    def deletePyloadFile(self, **kwargs):
        fid = kwargs.get('tag')

        try:
            response = self._api.deleteFile(fid=fid)
            if not response is None and response.status_code == 200:
                self._guiManager.setToastNotification(self._t.getString(PYLOAD_NOTIFICATION),
                                                      self._t.getString(PYLOAD_DELETED_SUCCESFULLY),
                                                      icon=self._OK_ICON)

                xbmc.executebuiltin('Container.Refresh')

        except requests.exceptions.ConnectionError as e:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(SERVER_NOT_REACHABLE), icon=self._ERROR_ICON)


    def restartPyloadFile(self, **kwargs):
        fid = kwargs.get('tag')

        try:
            response = self._api.restartFile(fid=fid)
            if not response is None and response.status_code == 200:
                self._guiManager.setToastNotification(self._t.getString(PYLOAD_NOTIFICATION),
                                                      self._t.getString(PYLOAD_RESTARTED_SUCCESFULLY), icon=self._OK_ICON)

                xbmc.executebuiltin('Container.Refresh')

        except requests.exceptions.ConnectionError as e:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(SERVER_NOT_REACHABLE),icon=self._ERROR_ICON)

    def restartPyloadPackage(self, **kwargs):
        pid = kwargs.get('tag')
        raise NotImplementedError

    def restartPyloadFailed(self, **kwargs):
        try:
            response = self._api.restartFailed()
            if not response is None and response.status_code == 200:
                self._guiManager.setToastNotification(self._t.getString(PYLOAD_NOTIFICATION),
                                                      self._t.getString(PYLOAD_RESTARTED_SUCCESFULLY),
                                                      icon=self._OK_ICON)

                xbmc.executebuiltin('Container.Refresh')

        except requests.exceptions.ConnectionError as e:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(SERVER_NOT_REACHABLE), icon=self._ERROR_ICON)


    def handlePyLoadErrorResponse(self, response):
        if not response is None:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(PYLOAD_STATUS_CODE) + f' ({response.status_code}) {response.reason}',icon=self._ERROR_ICON)

        else:
            self._guiManager.setToastNotification(self._t.getString(PYLOAD_ERROR),
                                                  self._t.getString(PYLOAD_ERROR_UNKOWN),icon=self._ERROR_ICON)

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

    def run(self):
        args = get_query_args(sys.argv[2])

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
            'markmail':     self.markMail,
            'add':          self.addEntity,
            'addall':       self.addMails,
            'deleteall':    self.deleteMails,
            'move':         self.moveEntity,
            'delete':       self.deleteEntity,
            'restart':      self.restartEntity
        }[method](param=param, page=page, tag=tag, navigation=navigation)

        self._guiManager.endOfDirectory()
