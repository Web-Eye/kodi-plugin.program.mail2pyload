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
import json

import requests

class pyloadAPI:

    def __init__(self, server, port, username, password):

        self._baseURL = f'http://{server}:{port}/api/'
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        }
        payload = {}
        formdata = {
            'username': (None, username),
            'password': (None, password),
        }

        self._session = requests.Session()
        self._session.post(f'{self._baseURL}login', headers=self._headers, data=payload, files=formdata)


    def getQueue(self):
        return self._session.post(f'{self._baseURL}getQueue', headers=self._headers)

    def getCollector(self):
        return self._session.post(f'{self._baseURL}getCollector', headers=self._headers)

    def addPackage(self, name, link):
        data = {
            'name': name,
            'links': [link],
            'dest': 0
        }

        payload = {k: json.dumps(v) for k, v in data.items()}
        return self._session.post(f'{self._baseURL}addPackage', headers=self._headers, data=payload)

    def addFiles(self, pid, link):
        data = {
            'package_id': pid,
            'links': [link]
        }

        payload = {k: json.dumps(v) for k, v in data.items()}
        return self._session.post(f'{self._baseURL}addFiles', headers=self._headers, data=payload)

    def movePackage(self, pid, destination):
        data = {
            'package_id': pid,
            'destination': destination
        }

        payload = {k: json.dumps(v) for k, v in data.items()}
        return self._session.post(f'{self._baseURL}movePackage', headers=self._headers, data=payload)

    def deletePackage(self, pid):
        data = {
            'package_ids': [pid]
        }

        payload = {k: json.dumps(v) for k, v in data.items()}
        return self._session.post(f'{self._baseURL}deletePackages', headers=self._headers, data=payload)

    def getPackageInfo(self, pid):
        data = {
            'package_id': pid
        }
        payload = {k: json.dumps(v) for k, v in data.items()}
        return self._session.post(f'{self._baseURL}getPackageInfo', headers=self._headers, data=payload)