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


import logging
import ircpacket as ircp
from irctools import require_public, load_textfile
from itertools import zip_longest


__plugin_description__ = 'Start the party on the seas!'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'command'
__plugin_enabled__ = True


DEFAULT_MSG = 'party boat!'


@require_public
def command(arg: tuple, packet: ircp.Packet, shared: dict):
    """
    Prints out a party boat to the chat
    """
    words = list(arg[1:])
    print('words: {}'.format(words))

    if len(words) == 0:
        words = list(DEFAULT_MSG.split(' '))
    if len(words) == 1:
        if len(words[0]) > 5:
            words.append(words[0][5:])
        else:
            words.append(' ')

    # CAPSLOCK IS CRUISE CONTROL FOR COOL
    words = [l.upper() for l in words]

    # [:5] is used to keep the argument length to five characters
    # The string '123456' is used to make sure that the zip pairs is at least 5 tuples long

    zip_pairs = tuple(zip_longest(words[0][:5], words[1][:5], '123456', fillvalue=' '))

    message = []

    for num, line in enumerate(shared['boat']):
        boat_line = ''

        if num != 5:
            first_letter = zip_pairs[num][0]
            second_letter = zip_pairs[num][1]

            if num == 0:  # the first line of the boat thing has 3 arguments
                name = ''

                # pad name to at least 11 chars
                if len(packet.sender) <= 11:
                    name = packet.sender + ' ' * (11 - len(packet.sender)) + '1,11|'
                else:
                    name = packet.sender

                boat_line = line.format(first_letter, second_letter, name)
            else:
                boat_line = line.format(first_letter, second_letter)
        else:  # on the sixth line, there is no formatting
            boat_line = line
        message.append(ircp.make_message(boat_line, packet.target))

    return message


def setup_resources(config: dict, shared: dict):
    '''
    Plugin callback to set up shared resources.
    '''
    import os.path
    shared['boat'] = load_textfile(os.path.join(shared['dir'], 'data/boat.txt'))
    logging.info('boat loaded')

    shared['help']['partyboat'] = 'Start the party boat! || :partyboat [word1] [word2] || :partyboat Hail Hydra'
    shared['help']['pb'] = 'Alias to the :partyboat command'
    shared['cooldown']['partyboat'] = 8
    shared['cooldown']['pb'] = 'partyboat'


def setup_commands(all_parsers):
    '''
    Plugin callback to set up commands associated with this plugin.
    '''

    all_parsers['partyboat'] = command
    all_parsers['pb'] = command
