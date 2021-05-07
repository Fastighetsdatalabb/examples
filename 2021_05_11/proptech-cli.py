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
# Minimal Proptech OS test CLI for testing some basic fetching of ProptecOS
# data.
# Author: Joakim Eriksson, RISE
#
import cmd, sys
import requests, urllib.parse
import json
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class ProptechCmd(cmd.Cmd):
    intro = 'Welcome to the proptech cmd shell.   Type help or ? to list commands.\n'
    prompt = '>>'
    
    def do_connect(self, line):
        'Connect to Proptech OS: connect <client id> <secret>'
        args = line.split()
        if (len(args) < 2):
            print("Error - you need to provide two arguments.")
            return
        cid = args[0]
        secret = args[1]
        if (len(args) > 2):
            owner=args[2]
        url = 'https://login.microsoftonline.com/d4218456-670f-42ad-9f6a-885ae15b6645/oauth2/v2.0/token'

        mydata = {
            'grant_type':'client_credentials',
            'client_id': cid,
            'client_secret': secret,
            'scope':'https://proptechos.com/api/.default'
        }

        response = requests.post(url, data = mydata)
        token = response.json()
        self.hdrs = {'accept':'application/json', 'Authorization': 'Bearer ' + token['access_token']}
        if owner:
            self.hdrs['X-Property-Owner'] = owner
        print("Sending fetch requests with token: ", self.hdrs)
    
    def do_fetch(self, line):
        'Get the list of resource from Proptech OS. fetch <type-of-resource> [number]'
        # Get the resource list - first 50 devices
        args = line.split()
        if (len(args) < 1):
            print("Error - you need to provide at least the resource type.")
            return
        type = args[0]
        size = 10
        extra = ''
        sizeStr = ''
        if (len(args) > 1):
            size = int(args[1])
            if size > 0:
                sizeStr = "?page=0&size=" + str(size)
            else:
                sizeStr = "?"
        if (len(args) > 2):
            if len(sizeStr) > 1:
                extra= "&" + args[2]
            else:
                extra = args[2]

        url = "https://proptechos.com/api/json/" + type + sizeStr + extra
        print("Fetching ", size, " of resource: ", type, " URL:", url)
#       devs = requests.get("https://proptechos.com/api/json/" + type + "?page=0&size=" + str(size) + extra, headers = self.hdrs)
        devs = requests.get(url, headers = self.hdrs)
        print(json.dumps(devs.json(), indent=4))
        self.result = devs.json()

    def do_eval(self, line):
        result = self.result
        devices = self.devices
        evalRes = eval(line)
        print(evalRes)

    def do_EOF(self, line):
        return True

    def do_save(self, line):
        'Save the last result as JSON. save <name>'
        with open(line, 'w') as data_file:
            json.dump(self.result, data_file, indent=4)
        print("Save to: ", line)

    def do_resolve_id(self, line):
        self.do_fetch("actuator 10 deviceIds=" + line)
        print(self.result)

    def do_plot_tag(self, line):
        self.do_fetch("sensor 10 littera=" + line)
        id = self.result['content'][0]['id']
        qKind = self.result['content'][0]['deviceQuantityKind']
        nowTime = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%dT%H:%MZ")
        oldTime = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(hours=12), "%Y-%m-%dT%H:%MZ")
        nowTime = urllib.parse.quote(nowTime)
        oldTime = urllib.parse.quote(oldTime)
        self.do_fetch("sensor/" + id + "/observation 0 startTime=" + oldTime + "&endTime=" + nowTime)
        data = self.result
        dates = list(map(lambda x: datetime.datetime.strptime(x['observationTime'], "%Y-%m-%dT%H:%M:%SZ"), data))
        y_values = list(map(lambda x: x['value'], data))
        x_values = dates
        fig, ax = plt.subplots()
        fig.autofmt_xdate()
        formatter = mdates.DateFormatter("%Y-%m-%d %H:%M")
        ax.xaxis.set_major_formatter(formatter)
        #locator = mdates.DayLocator()
        #ax.xaxis.set_major_locator(locator)
        plt.title("TAG: " + line)
        plt.ylabel(qKind)
        plt.xlabel("Time")
        plt.plot(x_values, y_values)
        plt.show()


    def do_plot_device(self, line):
        'plot device sensors last 12 hours'


    def do_quit(self, line):
        sys.exit()
    #
    # Device Id and keys file
    #
    def do_list_devices(self, line):
        for dev in self.devices:
            print(dev)

    def do_load_devices(self, line):
        with open(line, 'r') as data_file:
            data = data_file.read()
            self.devices = json.loads(data)

if __name__ == '__main__':
    cmd = ProptechCmd()
    cmd.result = []
    cmd.cmdloop()
