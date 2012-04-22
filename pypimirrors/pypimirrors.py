#!/usr/bin/env python

# -*- coding: utf-8 -*-
# Open Source Initiative OSI - The MIT License (MIT):Licensing
#
# The MIT License (MIT)
# Copyright (c) 2012 Ken Cochrane (KenCochrane@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

""" This is a simple library that you can use to find out the status of 
PyPI mirrors. It is based on the information that is found at
http://www.python.org/dev/peps/pep-0381/ and
http://pypi.python.org/mirrors
"""
import datetime
import socket
import urllib2
import time
import operator

MIRROR_URL_FORMAT = "http://{0}/last-modified"
MASTER_URL_FORMAT = "http://{0}/daytime"
MASTER_SERVER = "a.pypi.python.org"
LAST_SERVER = "last.pypi.python.org"
MIRROR_SUFFIX= "pypi.python.org"

STATUSES = {'GREEN':'Green',
            'YELLOW':'Yellow',
            'RED':'Red'}


def get_official_mirrors():
    """ Gets the list of official pypi mirrors

    http://pypi.python.org/mirrors """

    res = socket.gethostbyname_ex(LAST_SERVER)[0]
    last, dot, suffix = res.partition('.')
    assert suffix == MIRROR_SUFFIX
    mirrors = []
    # the mirrors start with b.pypi.python.org
    for l in range(ord('b'), ord(last) + 1):
        mirrors.append('{0:c}.{1}'.format(l, suffix))
    return mirrors


def ping_mirror(mirror_url):
    """ Given a mirror_url it will ping it and return the contents and
        the response time """
    try:
        start = time.time()
        res = urllib2.urlopen(mirror_url)
        stop = time.time()
        response_time = round((stop - start) * 1000, 2)
        return res.read().strip(), response_time
    except Exception:
        return None, None


def parse_date(date_str):
    """ parse the date the get back from the mirror """

    if len(date_str) == 17:
        # Used on official mirrors
        date_fmt = '%Y%m%dT%H:%M:%S'
    else:
        # Canonical ISO-8601 format (compliant with PEP 381)
        date_fmt = '%Y-%m-%dT%H:%M:%S'
    return datetime.datetime.strptime(date_str, date_fmt)


def humanize_date_difference(now, other_date=None, offset=None, sign="ago"):
    """ This function prints the difference between two python datetime objects
    in a more human readable form
    """

    if other_date:
        dt = abs(now - other_date)
        delta_d, offset = dt.days, dt.seconds
        if now < other_date:
            sign = "ahead"
    elif offset:
        delta_d, offset = divmod(offset, 60 * 60 * 24)
    else:
        raise ValueError("Must supply other_date or offset (from now)")

    offset, delta_s = divmod(offset, 60)
    delta_h, delta_m = divmod(offset, 60)

    if delta_d:
        fmt = "{d:d} days, {h:d} hours, {m:d} minutes {ago}"
    elif delta_h:
        fmt = "{h:d} hours, {m:d} minutes {ago}"
    elif delta_m:
        fmt = "{m:d} minutes, {s:d} seconds {ago}"
    else:
        fmt = "{s:d} seconds {ago}"
    return fmt.format(d=delta_d, h=delta_h, m=delta_m, s=delta_s, ago=sign)


def mirror_status_desc(how_old):
    """ Get the status description of the mirror """

    if how_old < datetime.timedelta(minutes=60):
        return STATUSES.get('GREEN')
    elif how_old < datetime.timedelta(days=1):
        return STATUSES.get('YELLOW')
    else:
        return STATUSES.get('RED')


def ping_master_pypi_server(master_url_format=MASTER_URL_FORMAT):
    """ Ping the master Pypi server, it is a little different
        then the other servers. """
    # a.pypi.python.org is the master server treat it differently
    m_url = master_url_format.format(MASTER_SERVER)
    res, res_time = ping_mirror(m_url)
    return MASTER_SERVER, res, res_time


def mirror_statuses(mirror_url_format=MIRROR_URL_FORMAT,
                    unofficial_mirrors=None,
                    mirrors=None,
                    ping_master_mirror=True):
    """ get the data we need from the mirrors and return a list of 
    dictionaries with information about each mirror

    ``mirror_url_format`` - Change the url format from the standard one

    ``unofficial_mirrors`` - Add a list of unofficial mirrors to test.
    The list needs to contain one string with just the domain for example.
    ['pypi.example.com',]

    ``mirrors`` - provided the list if mirrors to check, if None it will
    use the official PyPI mirrors. The list needs to contain one string
    with just the domain for example:
    ['pypi.example.com', 'pypi2.example.com']

    ``ping_master_mirror`` - Do you want to include the status of the master
    server in the results. Defaults to True.

    """
    # build up the list of mirrors to scan
    if not mirrors:
        mirrors = get_official_mirrors()
    if unofficial_mirrors:
        mirrors.extend(unofficial_mirrors)

    # scan the mirrors and collect data
    ping_results = []
    for ml in mirrors:
        m_url = mirror_url_format.format(ml)
        res, res_time = ping_mirror(m_url)
        ping_results.append((ml, res, res_time))

    if ping_master_mirror:
        # a.pypi.python.org is the master server treat it differently
        master_results = ping_master_pypi_server()
        ping_results.insert(0, master_results)

    now = datetime.datetime.utcnow()
    results = []
    for ml, res, res_time in ping_results:
        if res:
            last_update = parse_date(res)
            time_diff = abs(now - last_update)
            status = mirror_status_desc(time_diff)
            time_diff_human = humanize_date_difference(now, last_update)
            results.append({'mirror': ml,
                'last_update': last_update,
                'time_now': now,
                'time_diff': time_diff,
                'time_diff_human':  time_diff_human,
                'response_time': res_time,
                'status': status}
            )
        else:
            results.append({'mirror': ml,
                'last_update': "Unavailable",
                'time_now': now,
                'time_diff_human':  "Unavailable",
                'time_diff': 'Unavailable',
                'response_time':  "Unavailable",
                'status': 'Unavailable'}
            )
    return results


def is_master_alive():
    """ Check if the Master server is alive """
    server, response, res_time = ping_master_pypi_server()
    if response is None:
        return False
    return True


def find_out_of_date_mirrors(mirrors=None, unofficial_mirrors=None):
    """ Find the mirrors that are out of date """
    results = mirror_statuses(mirrors=mirrors,
                              unofficial_mirrors=unofficial_mirrors)
    bad_mirrors = []
    for r in results:
        if r.get('status') == STATUSES.get('RED'):
            bad_mirrors.append(r)
    return bad_mirrors


def __find_mirror_sort(sort_field, mirrors=None, unofficial_mirrors=None,
                       reverse=False):
    """ Find the first mirror that is sorted by sort_field """
    results = mirror_statuses(mirrors=mirrors, ping_master_mirror=False,
                              unofficial_mirrors=unofficial_mirrors)
    new_list = sorted(results, key=operator.itemgetter(sort_field), reverse=reverse)
    return new_list[0]


def find_fastest_mirror(mirrors=None, unofficial_mirrors=None):
    """ Find the fastest mirror (via response time), might not be up to date """
    return __find_mirror_sort('response_time', mirrors=mirrors,
                              unofficial_mirrors=unofficial_mirrors)


def find_freshest_mirror(mirrors=None, unofficial_mirrors=None):
    """ Find the freshest mirror (via last updated) """
    return __find_mirror_sort('time_diff', mirrors=mirrors,
                               unofficial_mirrors=unofficial_mirrors)
