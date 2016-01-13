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


__plugin_name__ = 'told'
__plugin_description__ = 'Get told'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'command'
__plugin_enabled__ = True

CLR_HGLT = '3'
CLR_RESET = ''
CLR_NICK = '11'

from os import path
from random import sample
#import argparse
import logging
import ircpacket as ircp


def told_command(arg, packet, shared, is_told=True):
    """
    Tells a user that they got told

    is_told - if True: user is told, else: user is not told
    """
    person = ''
    if len(arg) < 2:
        return ircp.make_notice('You need to specify who got told', packet.sender)
    else:
        person = ' '.join(arg[1:])

    logging.info('telling {}'.format(person))

    told_tuple = shared['told.tuple']

    checked = '[X] '
    unchecked = '[ ] '

    random_told = sorted(sample(told_tuple[2:], 3), key=len)

    if is_told:  # Use appropriate checkboxes if using `told` or `nottold`
        tolds = [unchecked + told_tuple[0], checked + told_tuple[1],
                 checked + random_told[0], checked + random_told[1], checked + random_told[2]]
    else:
        tolds = [checked + told_tuple[0], unchecked + told_tuple[1],
                 unchecked + random_told[0], unchecked + random_told[1], unchecked + random_told[2]]
    tolds = [phrase for phrase in tolds]

    # throttler.add_message()

    return ircp.make_message(('{0}{1}{2} just got: {3[0]} {3[1]} {3[2]} '
                              '{3[3]} {3[4]}').format(CLR_NICK, person, CLR_RESET, tolds), packet.target)


def nottold_command(arg, packet, shared):
    """
    Runs told_command with is_told=True
    """
    return told_command(arg, packet, shared, is_told=False)


def setup_resources(config: dict, shared: dict):
    from os import path
    with open(path.join(shared['dir'], 'data/told.txt')) as f:
        shared['told.tuple'] = tuple(line.strip() for line in f)
    logging.info('loaded party boat :D')

    shared['help']['told'] = 'Get told hard - :told <person>'
    shared['help']['nottold'] = 'Don\'t get told - :nottold <person>'

def setup_commands(all_commands: dict):
    all_commands['told'] = told_command
    all_commands['nottold'] = nottold_command
