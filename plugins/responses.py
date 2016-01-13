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


__plugin_name__ = 'responses'
__plugin_description__ = 'Respond to messages from the users.'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'regex'
__plugin_enabled__ = True


import re
import ircpacket as ircp


#CLR_HGLT = '3'
CLR_RESET = ''
CLR_NICK = '11'


def respond_greeting(regex, packet: ircp.Packet, shared: dict) -> str:
    ''' Respond to a nice greeting '''
    return packet.reply('Hey there, {1}{0}{2}!'.format(packet.sender, CLR_NICK, CLR_RESET))


def respond_good(regex, packet: ircp.Packet, shared: dict) -> str:
    ''' Respond to a good message '''
    return packet.reply('Thanks, {1}{0}{2}!'.format(packet.sender, CLR_NICK, CLR_RESET))


def respond_bad(regex, packet: ircp.Packet, shared: dict) -> str:
    ''' Respond to an ugly, mean message '''
    return packet.reply('Fuck you too, {1}{0}{2}!'.format(packet.sender, CLR_NICK, CLR_RESET))


def setup_resources(config: dict, shared: dict):
    greeting_re = re.compile('.*(hi|hello|howdy|greetings|salutations|salve|hola|hey|ahoy).{{0,3}}{0}'.format(config['bot_nick']),
                             re.IGNORECASE)
    good_re = re.compile('(\001ACTION)?.{{0,6}}(kiss(es)?|good|pats|pets|love|loves).{{0,6}}{0}.*'.format(config['bot_nick']), re.IGNORECASE)
    bad_re = re.compile('(\001ACTION)?.{{0,8}}(fucks?|pisses|piss|kills?|hates?).{{0,6}}{0}.*'.format(config['bot_nick']), re.IGNORECASE)

    shared['regexes']['greeting_re'] = greeting_re
    shared['regexes']['good_re'] = good_re
    shared['regexes']['bad_re'] = bad_re

    shared['re_response']['greeting_re'] = respond_greeting
    shared['re_response']['good_re'] = respond_good
    shared['re_response']['bad_re'] = respond_bad


def setup_commands(all_commands: dict):
    pass

