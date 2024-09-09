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

HOME = 'home'
NEW_MAIL = 'new_mail'
PYLOAD_PACKAGE = 'pyload_package'
PYLOAD_QUEUE = 'pyload_queue'
PYLOAD_COLLECTOR = 'pyload_collector'
ERROR = 'error'
IMAP_ERROR = 'imap_error'
SERVER_NOT_REACHABLE = 'imap_server_not_reachable'
SERVER_REFUSED = 'imap_server_not_reachable'
MARK_MAIL_SEEN = 'mark_mail_seen'
MARK_MAIL_DONE = 'mark_mail_done'
MARK_MAIL_DELETED = 'mark_mail_deleted'
PYLOAD_ERROR = 'pyload_error'
PYLOAD_ERROR_UMNKOWN = 'pyload_error_unkown'
PYLOAD_STATUS_CODE = 'pyload_status_code'
PYLOAD_ADDTO_PACKAGE = 'pyload_addto_package'

class Translations:

    def __init__(self, addon):
        self._language = addon.getLocalizedString

    def getString(self, name):

        return {
            HOME:                       self._language(30100),
            NEW_MAIL:                   self._language(30101),
            PYLOAD_PACKAGE:             self._language(30102),
            PYLOAD_QUEUE:               self._language(30106),
            PYLOAD_COLLECTOR:           self._language(30107),
            ERROR:                      self._language(30200),
            IMAP_ERROR:                 self._language(30201),
            SERVER_NOT_REACHABLE:       self._language(30202),
            SERVER_REFUSED:             self._language(30203),
            PYLOAD_ERROR:               self._language(30204),
            PYLOAD_ERROR_UMNKOWN:       self._language(30205),
            PYLOAD_STATUS_CODE:         self._language(30206),
            MARK_MAIL_SEEN:             self._language(30103),
            MARK_MAIL_DONE:             self._language(30104),
            MARK_MAIL_DELETED:          self._language(30105),
            PYLOAD_ADDTO_PACKAGE:       self._language(30108)

        }[name]
