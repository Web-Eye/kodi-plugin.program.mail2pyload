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


class mailParser:

    def __init__(self, server, port, username, password, folder, hoster_whitelist, hoster_blacklist):
        self._IMAP_SERVER = server
        self._IMAP_PORT = port
        self._IMAP_USERNAME = username
        self._IMAP_PASSWORD = password
        self._IMAP_FOLDER = folder
        self._HOSTER_WHITELIST = hoster_whitelist
        self._HOSTER_BLACKLIST = hoster_blacklist

    @property
    def getNewMails(self):

        retValue = []
        msg_encoding = 'us-ascii'

        with imaplib.IMAP4_SSL(host=self._IMAP_SERVER, port=self._IMAP_PORT) as imapCon:
            imapCon.login(user=self._IMAP_USERNAME, password=self._IMAP_PASSWORD)
            imapCon.select(self._IMAP_FOLDER)
            result, data = imapCon.uid('search', None, 'UNFLAGGED')

            uids = data[0]
            uid_list = uids.split()

            if len(uid_list) > 0:
                for uid in uid_list:
                    result, data = imapCon.uid('fetch', uid, '(RFC822)')
                    raw_email = data[0][1].decode("utf-8")
                    message = email.message_from_string(raw_email)
                    subject = str(make_header(decode_header(message['subject'])))

                    item = {
                        'uid': uid,
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
                        body = multi.get_payload(decode=True).decode(encoding=msg_encoding)

                    content = BeautifulSoup(body, 'lxml')
                    images = content.findAll('img')
                    for i in images:
                        item['images'].append(i['src'])

                    # detailBlock = content.findAll('div', class_='content')
                    detailBlock = content.find('div', id=re.compile('news.*'))


                    test = detailBlock.find()
                    package = None
                    for t in test:
                        if t.name is None:
                            if i != '':
                                if item['description'] is None:
                                    item['description'] = t
                                else:
                                    if package:
                                        item['packages'].append(package)
                                    package = {
                                        'subject': t,
                                        'hosters': []
                                    }

                        elif t.name == 'a' and t.find('img') is None and t.has_attr('href'):
                            h = ''.join(['' if ord(i) < 20 else i for i in t.getText()])
                            if h != '' and t['href'] != '':
                                hoster = {
                                    'subject': h,
                                    'link': t['href']
                                }

                                package['hosters'].append(hoster)

                    if package:
                        item['packages'].append(package)

                    retValue.append(item)

            imapCon.logout()

        return retValue



