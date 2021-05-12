#!/usr/bin/env python3
#
# Copyright (c) 2021, Nordomatic AB
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the owner nor the names of its contributors may be
#     used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ----------------------------------------------------------------------------
#
# Minimal Proptech OS library for basic fetching of ProptechOS data.
# Author: Joakim Eriksson, RISE
#
import urllib.parse
from datetime import datetime, timedelta

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import requests


def format_datetime(time):
    return datetime.strftime(time, "%Y-%m-%dT%H:%MZ")


class ProptechConnection:

    headers = None
    result = None

    def __init__(self, cid, secret, owner=None):
        self.result = []
        url = 'https://login.microsoftonline.com/d4218456-670f-42ad-9f6a-885ae15b6645/oauth2/v2.0/token'

        my_data = {
            'grant_type': 'client_credentials',
            'client_id': cid,
            'client_secret': secret,
            'scope': 'https://proptechos.com/api/.default'
        }

        response = requests.post(url, data=my_data)
        token = response.json()
        self.headers = {'accept': 'application/json', 'Authorization': 'Bearer ' + token['access_token']}
        if owner:
            self.headers['X-Property-Owner'] = owner
        print("Sending fetch requests with token:", self.headers)

    def fetch(self, resource_type, size=10, extra=''):
        """Get the list of resource from Proptech OS. fetch <type-of-resource> [number]"""
        # Get the resource list - first 50 devices
        if size > 0:
            size_attr = "?page=0&size=" + str(size)
        else:
            size_attr = "?page=0"
        if len(extra) > 0:
            extra = '&' + extra

        url = "https://proptechos.com/api/json/" + resource_type + size_attr + extra
        if size > 0:
            print("Fetching up to", size, "items of resource type", resource_type, " URL:", url)
        else:
            print("Fetching all items of resource type", resource_type, " URL:", url)
        devs = requests.get(url, headers=self.headers)
        self.result = devs.json()
        return self.result

    def resolve_id(self, device_id):
        return self.fetch("actuator", 10, "deviceIds=" + device_id)

    # fetch data from a sensor
    def fetch_data(self, device_id, size=0, end_time=None, start_time=None, hours=12):
        if not end_time:
            end_time = format_datetime(datetime.now())
        if not start_time:
            start_time = format_datetime(datetime.now() - timedelta(hours=hours))
        end_time = urllib.parse.quote(end_time)
        start_time = urllib.parse.quote(start_time)
        return self.fetch("sensor/" + device_id + "/observation", size,
                          "startTime=" + start_time + "&endTime=" + end_time)

    def plot_tag(self, line):
        json_data = self.fetch("sensor", 10, "littera=" + line)
        device_id = json_data['content'][0]['id']
        q_kind = json_data['content'][0]['deviceQuantityKind']
        data = self.fetch_data(device_id)
        self.plot_data('TAG: ' + line, q_kind, data)

    def plot_data(self, title, y_label, data):
        dates = list(map(lambda x: datetime.strptime(x['observationTime'], "%Y-%m-%dT%H:%M:%SZ"), data))
        y_values = list(map(lambda x: x['value'], data))
        x_values = dates
        fig, ax = plt.subplots()
        fig.autofmt_xdate()
        formatter = mdates.DateFormatter("%Y-%m-%d %H:%M")
        ax.xaxis.set_major_formatter(formatter)
        # locator = mdates.DayLocator()
        # ax.xaxis.set_major_locator(locator)
        plt.title(title)
        plt.ylabel(y_label)
        plt.xlabel("Time")
        plt.plot(x_values, y_values)
        plt.show()
