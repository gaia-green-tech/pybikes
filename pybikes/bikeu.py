# -*- coding: utf-8 -*-
# Copyright (C) 2015, thesebas <thesebas@thesebas.net>
# Distributed under the AGPL license, see LICENSE.txt
from __future__ import absolute_import
import re
import json
from six.moves.urllib.parse import urljoin

from lxml import html

from .base import BikeShareSystem, BikeShareStation
from . import utils
from six.moves import map

__all__ = ['Bikeu', 'BikeuStation']

REGEX = "setConfig('StationsData',([.*]));"

class Bikeu(BikeShareSystem):

    meta = {
        'system': 'Bike U',
        'company': ['Bike U Sp. z o.o.']
    }

    def __init__(self, tag, meta, url):
        super(Bikeu, self).__init__(tag, meta)
        self.url = url

    def parse_map(self, body):
        matched = re.search(REGEX, body)
        if not matched:
            return None
        markers = json.loads(matched.group(1))
        return markers

    def update(self, scraper=None):
        if scraper is None:
            scraper = utils.PyBikesScraper()

        body = scraper.request(self.url)
        markers = self.parse_map(body)
        if not markers:
            # Map data is on an iframe
            _html = html.fromstring(body)
            map_src = next(iter(_html.xpath('id("MapData")/@src')), None)
            if not map_src:
                raise Exception('No marker data found')
            map_src = urljoin(self.url, map_src)
            map_body = scraper.request(map_src)
            markers = self.parse_map(map_body)
        self.stations = list(map(BikeuStation, markers))


class BikeuStation(BikeShareStation):
    def __init__(self, info):
        super(BikeuStation, self).__init__()
        self.latitude = float(info['Latitude'])
        self.longitude = float(info['Longitude'])

        self.name = info['Name']
        self.bikes = int(info['TotalAvailableBikes'])
        self.free = int(info['TotalLocks']) - self.bikes
        # Assumedly there's bike info too
        bike_info = info['Stations']['TKStation'][0]['AvailableBikes']
        bikes = bike_info.get('TKBike', [])
        bike_uids = [b.get('BikeIdentifier') for b in bikes]
        bike_uids = [_f for _f in bike_uids if _f]
        self.extra = {
            'uid': info['id'],
        }
        if bike_uids:
            self.extra['bike_uids'] = bike_uids
