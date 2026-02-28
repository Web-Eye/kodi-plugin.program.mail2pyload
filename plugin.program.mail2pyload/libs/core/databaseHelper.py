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
from mysql import connector


class databaseHelper:

    @staticmethod
    def getMasterConnection(config):
        return connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password']
        )

    @staticmethod
    def createPool(config):
        return connector.connect(
            pool_name='mainPool',
            pool_size=10,
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )

    @staticmethod
    def get_connection():
        return connector.connect(
            pool_name='mainPool'
        )

    @staticmethod
    def executeScalar(con, query, parameters=None):
        retValue = None

        try:
            cursor = con.cursor()
            cursor.execute(query, parameters)
            row = cursor.fetchone()
            retValue = None
            if row is not None:
                retValue = row[0]

            cursor.close()
        except mysql.connector.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")

        return retValue

    @staticmethod
    def executeNonQuery(con, statement, parameters=None):
        row_count = None
        last_row_id = None

        try:
            cursor = con.cursor()
            cursor.execute(statement, parameters)

            last_row_id = cursor.lastrowid
            con.commit()
            row_count = cursor.rowcount

            cursor.close()

        except mysql.connector.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")

        return row_count or 0, last_row_id or 0

    @staticmethod
    def executeReader(con, query, parameters=None):

        try:
            cursor = con.cursor()
            cursor.execute(query, parameters)
            return cursor

        except mysql.connector.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            return None

    @staticmethod
    def database_exists(con, databasename):
        result = databaseHelper.executeScalar(con, 'SELECT COUNT(*) FROM INFORMATION_SCHEMA.SCHEMATA WHERE '
                                                   'SCHEMA_NAME = ?', (databasename,))
        if result == 1:
            return True

        return False

    @staticmethod
    def create_database(con, databasename):
        rows = databaseHelper.executeNonQuery(con, f'CREATE DATABASE {databasename}')
        return rows[0] == 1

    @staticmethod
    def tableExists(con, databasename, tablename):
        result = databaseHelper.executeScalar(con, 'SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA '
                                                   '= ? AND TABLE_NAME = ?', (databasename, tablename,))
        if result == 1:
            return True

        return False
