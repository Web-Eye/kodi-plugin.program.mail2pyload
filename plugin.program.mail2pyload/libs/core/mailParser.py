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

class mailParser:

    def __init__(self, server, port, username, password, folder, hoster_whitelist, hoster_blacklist):
        self._IMAP_SERVER = server
        self._IMAP_PORT = port
        self._IMAP_USERNAME = username
        self._IMAP_PASSWORD = password
        self._IMAP_FOLDER = folder
        self._HOSTER_WHITELIST = hoster_whitelist
        self._HOSTER_BLACKLIST = hoster_blacklist

    def getNewMails(self):

        with imaplib.IMAP4_SSL(host=self._IMAP_SERVER, port=self._IMAP_PORT) as imapCon:
            imapCon.login(user=self._IMAP_USERNAME, password=self._IMAP_PASSWORD)
            imapCon.select(self._IMAP_FOLDER)
            result, data = imapCon.uid('search', None, "ALL")

            uids = data[0]
            uid_list = uids.split()

            if len(uid_list) > 0:
                for uid in uid_list:
                    result, data = imapCon.uid('fetch', uid, '(RFC822)')
                    raw_email = data[0][1]
                    print(raw_email)

            imapCon.logout()





