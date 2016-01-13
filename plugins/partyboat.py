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


__plugin_name__ = 'partyboat'
__plugin_alias__ = 'pb'
__plugin_description__ = 'Start the party on the seas!'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'command'
__plugin_enabled__ = True


from os import path
#import argparse
import logging
from itertools import zip_longest
import ircpacket as ircp


DEFAULT_MSG = 'HAIL HYDRA'


def command(arg, packet, shared):
    """
    Prints out a party boat to the chat
    """
    print('The party just started')

    print('got {}'.format(arg))
    

    # Discard unwanted whitespace between words
    #arg = ' '.join(arg.split())
    words = arg[1:]

    if len(words) == 0:
        words = 'hail hydra'.split(' ')
    if len(words) == 1:
        if len(words[0]) > 5:
            words.append(words[0][5:])
        else:
            words.append(' ')

    # CAPSLOCK IS CRUISE CONTROL FOR COOL
    words = [l.upper() for l in words]

    if packet.target.lower() not in shared['chan']:
        error = 'Sorry. This command is for public-chat only'
        return ircp.make_notice(error, packet.sender)

    # [:5] is used to keep the argument length to five characters
    # The string '123456' is used to make sure that the zip pairs is at least 5 tuples long
    
    zip_pairs = tuple(zip_longest(words[0][:5], words[1][:5], '123456', fillvalue=' '))

    message = []

    for num, line in enumerate(shared['boat']):
        # boat_line = special_color + zip_pairs[num][0] + line + zip_pairs[num][1] + CLR_RESET 
        boat_line = ''

        if num != 5:
            first_letter = zip_pairs[num][0]
            second_letter = zip_pairs[num][1]

            if num == 0:  # the first line of the boat thing has 3 arguments
                name = ''

                # pad name to at least 6 chars
                if len(packet.sender) <= 6:
                    name = ' '*(6 - len(packet.sender)) + packet.sender
                else:
                    name = packet.sender

                boat_line = line.format(first_letter, second_letter, name)
            else:
                boat_line = line.format(first_letter, second_letter)
        else:  # on the sixth line, there is no formatting
            boat_line = line

        # Below is the LAME old formatting
        #if num == 0:
        #    boat_line += ' {1}{0}{2} started the partyboat!'.format(packet.sender, CLR_NICK, CLR_RESET)

        message.append(ircp.make_message(boat_line, packet.target))
    #print(line for line in message)
    return message


def setup_resources(config: dict, shared: dict):
    '''
    Plugin callback to set up shared resources.
    '''
    # don't care about config
    import os
    shared['boat'] = []
    for line in open(os.path.join(shared['dir'], 'data/boat.txt')):
        shared['boat'].append(line.replace('\n', ''))
    logging.info('boat loaded')
    print(shared['boat'])

    shared['help']['partyboat'] = 'Start the party boat! || :partyboat [word1] [word2] || :partyboat Hail Hydra'
    shared['help']['pb'] = 'Alias to the :partyboat command'
    shared['cooldown']['partyboat'] = 8
    shared['cooldown']['pb'] = 'partyboat'


def setup_commands(all_parsers):
    '''
    Plugin callback to set up commands associated with this plugin.
    '''

    all_parsers[__plugin_name__] = command
    all_parsers[__plugin_alias__] = command

