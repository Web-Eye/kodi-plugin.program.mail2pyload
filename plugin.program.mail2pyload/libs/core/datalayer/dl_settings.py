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

from ..databaseHelper import databaseHelper


class DL_settings:

    @staticmethod
    def existsSetting(con, name):
        c = databaseHelper.executeScalar(con, 'SELECT COUNT(*) FROM settings WHERE name = %s', (name, ))
        return c != 0

    @staticmethod
    def getSetting(con, name):
        cursor = databaseHelper.executeReader(con, 'SELECT value FROM settings WHERE name = %s', (name, ))
        row = cursor.fetchone()
        if row is not None:
            return row[0]

        return None

    @staticmethod
    def setSetting(con, name, value):
        if DL_settings.existsSetting(con, name):
            databaseHelper.executeNonQuery(con, 'UPDATE settings SET value = ? WHERE name = %s', (value, name,))
        else:
            databaseHelper.executeNonQuery(con, 'INSERT INTO settings (name, value) VALUES (%s, %s)', (name, value,))
