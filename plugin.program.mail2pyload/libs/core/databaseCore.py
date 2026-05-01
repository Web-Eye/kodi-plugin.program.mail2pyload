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

import mysql.connector

from .databaseHelper import databaseHelper
from .datalayer.dl_settings import DL_settings


class databaseCore:

    def __init__(self, **kwargs):
       databaseHelper.createPool(kwargs)

    @staticmethod
    def getrealdebritHosts():
        con = databaseHelper.get_connection()
        try:
            return DL_settings.getSetting(con, 'realdebrit_hosts')

        except mysql.connector.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            return False

        finally:
            con.close()

    @staticmethod
    def getrealdebritDomains():
        con = databaseHelper.get_connection()
        try:
            return DL_settings.getSetting(con, 'realdebrit_domains')

        except mysql.connector.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            return False

        finally:
            con.close()
