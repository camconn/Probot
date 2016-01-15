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


__plugin_description__ = 'Simple substitution using s/old/new/'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'combined'
__plugin_enabled__ = True


import re
import ircpacket as ircp
from irctools import CLR_RESET, CLR_ITLCS

REGEX_SUB ='^s/.*/.*(\/(g?))?$'


def sub_replace(regex, packet: ircp.Packet, shared: dict) -> str:
    """
    Naive substitution regular expression on previous message.
    """
    global_flag = False

    parts = packet.text.split('/')
    old, new = None, None
    
    old = parts[1]
    new = parts[2]
    if len(parts) >= 4:
        if parts[3].lower() == 'g':
            global_flag = True

    
    # Now, find the last message in the same channel that
    # contains `old`
    orig_packet = None
    output = ''

    print('looking for "{}"'.format(old))
    for p in reversed(shared['recent_messages']):
        if p.target == packet.target:
            if p.msg_public and (p.text.find(old) != -1):
                output = str(p.text)
                orig_packet = p
                break
    else:
        return packet.reply('Could not find a suitable substitution target.')


    print('replacing "{}" with "{}"'.format(old, new))
    print('original: "{}"'.format(output))
    # patch in italics
    new = CLR_ITLCS + new + CLR_RESET


    if global_flag:
        output = output.replace(old, new)
    else:
        output = output.replace(old, new, 1)

    return packet.reply('<{}> {}'.format(orig_packet.sender, output))


def setup_resources(config: dict, shared: dict):
    sub_re = re.compile(REGEX_SUB)

    shared['regexes']['sub_re'] = sub_re
    shared['re_response']['sub_re'] = sub_replace


def setup_commands(all_commands: dict):
    pass
