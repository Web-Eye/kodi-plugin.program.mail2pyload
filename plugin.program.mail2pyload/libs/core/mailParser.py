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
import email
import re
from email.header import make_header, decode_header
from bs4 import BeautifulSoup

from libs.common.tools import doLinkMatch, getBody, getCompiledRDRegExPattern, get_rddomain, replace_domain


class mailParser:

    def __init__(self, server, port, username, password, folder, hoster_whitelist_compiled, hoster_blacklist_compiled,
                 rd_hosterDict, rd_domainDict_compiled):
        self._IMAP_SERVER = server
        self._IMAP_PORT = port
        self._IMAP_USERNAME = username
        self._IMAP_PASSWORD = password
        self._IMAP_FOLDER = folder
        self._HOSTER_WHITELIST_COMPILED = hoster_whitelist_compiled
        self._HOSTER_BLACKLIST_COMPILED = hoster_blacklist_compiled
        self._RD_HOSTERDICT = rd_hosterDict
        self._COMPILED_RD_REGEX_PATTERN = None
        if rd_hosterDict:
            self._COMPILED_RD_REGEX_PATTERN = getCompiledRDRegExPattern(self._RD_HOSTERDICT)

        self._RD_DOMAINS_COMPILED = rd_domainDict_compiled


    def getNewMails(self):

        retValue = []
        msg_encoding = 'us-ascii'

        with imaplib.IMAP4_SSL(host=self._IMAP_SERVER, port=self._IMAP_PORT) as imapCon:
            imapCon.login(user=self._IMAP_USERNAME, password=self._IMAP_PASSWORD)
            imapCon.select(self._IMAP_FOLDER)
            result, data = imapCon.uid('search', None, 'UNFLAGGED UNDELETED')

            uids = data[0]
            uid_list = uids.split()

            if len(uid_list) > 0:
                for uid in uid_list:
                    result, data = imapCon.uid('fetch', uid, '(BODY.PEEK[])')
                    raw_email = data[0][1].decode("utf-8")
                    message = email.message_from_string(raw_email)
                    subject = str(make_header(decode_header(message['subject'])))

                    item = {
                        'uid': int(uid),
                        'subject': subject,
                        'description': None,
                        'images': [],
                        'packages': []
                    }

                    if not message.is_multipart():

                        single = bytearray(message.get_payload(), msg_encoding)
                        body = single.decode(encoding=msg_encoding)
                    else:
                        multi = message.get_payload()[0]
                        body = getBody(multi, msg_encoding)
                        # body = multi.get_payload(decode=True).decode(encoding=msg_encoding)

                    content = BeautifulSoup(body, 'html.parser')
                    images = content.findAll('img')
                    for i in images:
                        image = i.get('src')
                        if image is not None:
                            item['images'].append(image)

                    # detailBlock = content.findAll('div', class_='content')
                    detailBlock = content.find('div', id=re.compile('news.*'))
                    lastSubject = ''

                    test = detailBlock.find()
                    package = None
                    for t in test:
                        if t.name is None:
                            if i != '':
                                lastSubject = t
                                if item['description'] is None:
                                    item['description'] = t
                                else:
                                    if package and len(package.get('hosters')) > 0:
                                        item['packages'].append(package)
                                    package = {
                                        'subject': t,
                                        'hosters': []
                                    }

                        elif t.name == 'a' and t.find('img') is None and t.has_attr('href'):
                            h = ''.join(['' if ord(i) < 20 else i for i in t.getText()])
                            if h != '' and t.get('href') != '':
                                link = t.get('href')
                                _domain = get_rddomain(link, self._RD_DOMAINS_COMPILED)
                                link = replace_domain(link, _domain)

                                addit = False

                                if self._HOSTER_WHITELIST_COMPILED:
                                    match = self._HOSTER_WHITELIST_COMPILED.search(link)
                                    addit = (not match is None)

                                if not addit and self._RD_HOSTERDICT and len(self._RD_HOSTERDICT) > 0:
                                    addit = doLinkMatch(self._COMPILED_RD_REGEX_PATTERN, link)

                                if addit and self._HOSTER_BLACKLIST_COMPILED:
                                    match = self._HOSTER_BLACKLIST_COMPILED.match(link)
                                    addit = (match is None)

                                if addit:
                                    hoster = {
                                        'subject': h,
                                        'link': link
                                    }

                                    if not package:
                                        package = {
                                            'subject': lastSubject,
                                            'hosters': []
                                        }

                                    package['hosters'].append(hoster)

                    if package and len(package.get('hosters')) > 0:
                        item['packages'].append(package)

                    if len(item['packages']) > 0:
                        retValue.append(item)

            imapCon.logout()

        return retValue

    def setFlag(self, uid, flag, value):

        with imaplib.IMAP4_SSL(host=self._IMAP_SERVER, port=self._IMAP_PORT) as imapCon:
            imapCon.login(user=self._IMAP_USERNAME, password=self._IMAP_PASSWORD)
            imapCon.select(self._IMAP_FOLDER)

            arg1 = '-FLAGS'
            if value:
                arg1 = '+FLAGS'

            arg2 = {
                'SEEN':     '\\Seen',
                'DONE':     '\\Flagged',
                'DELETED':  '\\Deleted'
            }[flag]

            val1, val2 = imapCon.uid('store', uid, arg1, arg2)
            imapCon.logout()



