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


__plugin_name__ = 'rekt'
__plugin_description__ = 'Get rekt'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'command'
__plugin_enabled__ = True

# This is a direct translation of plugins/told.py

CLR_HGLT = '3'
CLR_RESET = ''
CLR_NICK = '11'

from os import path
from random import sample
#import argparse
import logging
import ircpacket as ircp


def rekt_command(arg, packet, shared, is_rekt=True):
    """
    Tells a user that they got rekt

    is_rekt - if True: user is rekt, else: user is not rekt
    """
    person = ''
    if len(arg) < 2:
        return ircp.make_notice('You need to specify who got rekt', packet.sender)
    else:
        person = ' '.join(arg[1:])

    logging.info('telling {}'.format(person))

    rekt_tuple = shared['rekt.tuple']

    checked = '[X] '
    unchecked = '[ ] '

    random_rekt = sorted(sample(rekt_tuple[2:], 3), key=len)

    if is_rekt:  # Use appropriate checkboxes if using `rekt` or `notrekt`
        rekts = [unchecked + rekt_tuple[0], checked + rekt_tuple[1],
                 checked + random_rekt[0], checked + random_rekt[1], checked + random_rekt[2]]
    else:
        rekts = [checked + rekt_tuple[0], unchecked + rekt_tuple[1],
                 unchecked + random_rekt[0], unchecked + random_rekt[1], unchecked + random_rekt[2]]
    rekts = [phrase for phrase in rekts]

    # throttler.add_message()

    return ircp.make_message(('{0}{1}{2} just got: {3[0]} {3[1]} {3[2]} '
                              '{3[3]} {3[4]}').format(CLR_NICK, person, CLR_RESET, rekts), packet.target)


def notrekt_command(arg, packet, shared):
    """
    Runs rekt_command with is_rekt=True
    """
    return rekt_command(arg, packet, shared, is_rekt=False)


def setup_resources(config: dict, shared: dict):
    from os import path
    with open(path.join(shared['dir'], 'data/rekt.txt')) as f:
        shared['rekt.tuple'] = tuple(line.strip() for line in f)
    logging.info('ready to get rekt?')

    shared['help']['rekt'] = 'Get rekt hard || :rekt <person> || :rekt your mum'
    shared['help']['notrekt'] = 'Don\'t get rekt || :notrekt <person> || :notrekt me'
    shared['cooldown']['rekt'] = 4
    shared['cooldown']['notrekt'] = 4

def setup_commands(all_commands: dict):
    all_commands['rekt'] = rekt_command
    all_commands['notrekt'] = notrekt_command
