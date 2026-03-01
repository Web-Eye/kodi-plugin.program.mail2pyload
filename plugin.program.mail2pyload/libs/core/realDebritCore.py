# -*- coding: utf-8 -*-
# Copyright 2026 WebEye
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
import requests

class realdebritCore:

    def __init__(self, token):
        self._token = token
        self._headers = {
            'Authorization': 'Bearer ' + self._token
        }

    def getHostsStatus(self):
        url = "https://api.real-debrid.com/rest/1.0/hosts/status"

        payload = {}
        response = requests.request("GET", url, headers=self._headers, data=payload)
        if response.status_code == 200:
            return response.json()

        return None

    def getHostsRegEx(self):
        url = "https://api.real-debrid.com/rest/1.0/hosts/regex"

        payload = {}
        response = requests.request("GET", url, headers=self._headers, data=payload)
        if response.status_code == 200:
            return response.json()

        return None

    def unrestrictLink(self, link):
        url = "https://api.real-debrid.com/rest/1.0/unrestrict/link"

        payload = f"link={link}"

        headers = self._headers.copy()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json()

        return None


