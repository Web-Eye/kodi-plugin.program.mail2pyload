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
import base64
import re
import urllib
import urllib.parse


def getBody(payload, msg_encoding):
    enc = payload['Content-Transfer-Encoding']
    if enc != 'base64':
        return payload.get_payload(decode=True).decode(encoding=msg_encoding)
    else:
        return base64.b64decode(payload.get_payload())

def doLinkMatch(compiledRegExPattern, link):
    return any(rx.search(link) for p, rx in compiledRegExPattern)

def getCompiledRDRegExPattern(hosterDict):
    regExPatterns = []
    for key, value in hosterDict.items():
        patterns = value.get("regex")
        if not patterns:
            continue

        if isinstance(patterns, list):
            regExPatterns.extend(patterns)
        else:
            regExPatterns.append(patterns)

    return [(p, re.compile(p, re.IGNORECASE)) for p in regExPatterns if p]

def get_highest_prio_match(prios, candidates):
    for pattern in prios:
        regex = re.compile(pattern)
        for s in candidates:
            if regex.search(s):
                return s
    return candidates[0]

def base64Encode(s):
    b = s.encode("ascii")

    encoded = base64.b64encode(b)
    return encoded.decode("ascii")


def base64Decode(s):
    b = s.encode("ascii")
    decoded = base64.b64decode(b)
    return decoded.decode("ascii")

def get_query_args(s_args):
    args = urllib.parse.parse_qs(urllib.parse.urlparse(s_args).query)

    for key in args:
        args[key] = args[key][0]
    return args

def formatSize(b):
    i = 0
    while b > 1024:
        i += 1
        b /= 1024

    if i > 0:
        b = '{:.2f}'.format(b)

    if i == 0:
        return f'{b} B'
    elif i == 1:
        return f'{b} KiB'
    elif i == 2:
        return f'{b} MiB'
    elif i == 3:
        return f'{b} GiB'
    elif i == 4:
        return f'{b} TiB'
    elif i == 5:
        return f'{b} PiB'
    elif i == 6:
        return f'{b} EiB'
    elif i == 7:
        return f'{b} ZiB'
    elif i == 8:
        return f'{b} YiB'

    return None