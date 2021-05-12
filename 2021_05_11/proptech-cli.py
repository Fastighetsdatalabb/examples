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
# Minimal Proptech OS test CLI for testing some basic fetching of ProptechOS
# data.
# Author: Joakim Eriksson, RISE
#
import cmd
import json
import sys
import urllib.parse
from datetime import datetime, timedelta

import proptech


class ProptechCmd(cmd.Cmd):
    intro = 'Welcome to the proptech cmd shell.   Type help or ? to list commands.\n'
    prompt = '>>'
    connection = None
    _devices = None

    @property
    def devices(self):
        return self._devices if self._devices else []

    @property
    def result(self):
        return self.connection.result if self.connection else []

    def do_connect(self, line):
        """Connect to Proptech OS: connect <client id> <secret>"""
        args = line.split()
        if len(args) < 2:
            print("Error - you need to provide two arguments.")
            return
        cid = args[0]
        secret = args[1]
        owner = args[2] if len(args) > 2 else None
        self.connection = proptech.ProptechConnection(cid, secret, owner)
        print("Sending fetch requests with token: ", self.connection.headers)

    def do_fetch(self, line):
        """Get the list of resource from Proptech OS. fetch <type-of-resource> [number]"""
        if not self.connection:
            print("Error - not connected.")
            return
        # Get the resource list - first 50 devices
        args = line.split()
        if len(args) < 1:
            print("Error - you need to provide at least the resource type.")
            return
        resource_type = args[0]
        size = int(args[1]) if len(args) > 1 else 10
        extra = args[2] if len(args) > 2 else ''
        json_data = self.connection.fetch(resource_type, size, extra)
        print(json.dumps(json_data, indent=4))

    def do_eval(self, line):
        result = self.result
        devices = self.devices
        eval_res = eval(line)
        print(eval_res)

    def do_EOF(self, line):
        return True

    def do_save(self, line):
        """Save the last result as JSON. save <name>"""
        with open(line, 'w') as data_file:
            json.dump(self.result, data_file, indent=4)
        print("Save to: ", line)

    def do_plot_tag(self, line):
        if not self.connection:
            print("Error - not connected.")
            return
        extra = 'littera=' + line if line else ''
        result_data = self.connection.fetch('sensor', size=10, extra=extra)
        device_id = result_data['content'][0]['id']
        q_kind = result_data['content'][0]['deviceQuantityKind']
        end_time = proptech.format_datetime(datetime.now())
        start_time = proptech.format_datetime(datetime.now() - timedelta(hours=12))
        end_time = urllib.parse.quote(end_time)
        start_time = urllib.parse.quote(start_time)
        data = self.connection.fetch_data('sensor/' + device_id + '/observation', size=0,
                                          end_time=end_time, start_time=start_time)
        self.connection.plot_data('TAG: ' + line, q_kind, data)

    def do_plot_device(self, line):
        """plot device sensors last 12 hours"""

    def do_quit(self, line):
        sys.exit()

    #
    # Device Id and keys file
    #
    def do_list_devices(self, line):
        for dev in self.devices:
            print(dev)

    def do_load_devices(self, line):
        if not line:
            print("Error: please specify a file with device information.")
            return
        try:
            with open(line, 'r') as data_file:
                data = data_file.read()
                self._devices = json.loads(data)
        except FileNotFoundError:
            print(f"Error: the file '{line}' does not exist.")


if __name__ == '__main__':
    cmd = ProptechCmd()
    cmd.cmdloop()
