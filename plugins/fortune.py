#!/usr/bin/env python3

# probot - An asynchronous IRC bot written in Python 3
# Copyright (c) 2016 Cameron Conn
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''
Fortune - Get a cute message from the Unix fortune utility

Also supports cowsay (if installed to $PATH)
'''


import os
from subprocess import check_output
import ircpacket as ircp


__plugin_description__ = 'Simple fortune utility'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'command'
__plugin_enabled__ = True


def which(program: str) -> str:
    ''' Simple which method.
    Thanks to http://stackoverflow.com/a/377028
    '''
    def _is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if _is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if _is_exe(exe_file):
                return exe_file
    return None


def fortune_command(arg: tuple, packet: ircp.Packet, shared: dict) -> str:
    ''' Tells the user a fortune (maybe via cowsay)

    :fortune - tells the user a fortune
    :cowsay - tells the user a fortune via cowsay
    :moo - alias of cowsay
    '''
    command = None
    if arg[0].lower() == 'fortune':
        command = '{} -a'.format(shared['fortune.path'])
    elif arg[0].lower() == 'cowsay':
        if 'fortune.cowsay' in shared:
            command = '{} -a | {}'.format(shared['fortune.path'], shared['fortune.cowsay'])
        else:
            return packet.notice('This machine does not have cowsay installed. '
                                 'Please install cowsay, then reload this plugin.')

    # rstrip to remove trailing newline
    ps = check_output(command, shell=True, universal_newlines=True).rstrip()
    print(ps)

    return (packet.notice(line) for line in ps.split('\n'))


def setup_resources(config: dict, shared: dict):
    fortune_path = which('fortune')
    if fortune_path:
        shared['fortune.path'] = fortune_path
    else:
        raise OSError('Could not find "fortune" executable. Disabling self.')

    # Optional cowsay command. If it isn't installed, it's no big deal
    cowsay_path = which('cowsay')
    if cowsay_path:
        shared['fortune.cowsay'] = cowsay_path

    shared['help']['fortune'] = 'Get a cute fortune || :fortune'
    shared['help']['cowsay'] = 'Get a fortune via cowsay || :cowsay'
    shared['help']['moo'] = 'Alias of :cowsay || :moo'
    shared['cooldown']['fortune'] = 5
    shared['cooldown']['cowsay'] = 7
    shared['cooldown']['moo'] = 'cowsay'


def setup_commands(all_commands: dict):
    all_commands['fortune'] = fortune_command
    all_commands['cowsay'] = fortune_command
    all_commands['moo'] = fortune_command

if __name__ == '__main__':
    # Just for testing, please ignore
    f_path = which('fortune')
    print('which "fortune": {}'.format(f_path))
    idiot_path = which('idiot')
    print('which "idiot": {}'.format(idiot_path))
