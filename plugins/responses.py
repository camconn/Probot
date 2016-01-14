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


CLR_HGLT = '3'
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


def respond_help(regex, packet: ircp.Packet, shared: dict) -> str:
    ''' Respond to general help regex '''
    return (ircp.make_notice('For a list of my commands, type {0}:commands{1}'.format(CLR_HGLT,
                                                                        CLR_RESET), packet.sender),
            ircp.make_notice('For help with a particular command, '  \
                         'type {0}:help commandname{1}'.format(CLR_HGLT, CLR_RESET), packet.sender))

def setup_resources(config: dict, shared: dict):

    nick = config['bot_nick']
    # Respond to friendly greetings
    greeting_re = re.compile('.*(hi|hello|howdy|greetings|salutations|salve|hola|hey|ahoy)\s(there)?.{{0,3}}{0}'.format(nick),
                             re.IGNORECASE)
    # Respond to nice things
    good_re = re.compile('(\001ACTION)?.{{0,6}}(kiss(es)?|good|pats|pets|love|loves).{{0,6}}{0}.*'.format(nick), re.IGNORECASE)
    # Respond to mean things
    bad_re = re.compile('(\001ACTION)?.{{0,8}}(fucks?|pisses|piss|kills?|hates?).{{0,6}}{0}.*'.format(nick), re.IGNORECASE)
    # Respond to cries for help
    help_re1 = re.compile('.*(help|commands).{{0,6}}((me|does|do).{{0,8}})?{0}.*'.format(nick), re.IGNORECASE)
    help_re2 = re.compile('.{{0,8}}{0}(\splease\s)?.{{0,3}}(help|halp).*'.format(nick), re.IGNORECASE)

    shared['regexes']['greeting_re'] = greeting_re
    shared['regexes']['good_re'] = good_re
    shared['regexes']['bad_re'] = bad_re
    shared['regexes']['help_re1'] = help_re1
    shared['regexes']['help_re2'] = help_re2

    shared['re_response']['greeting_re'] = respond_greeting
    shared['re_response']['good_re'] = respond_good
    shared['re_response']['bad_re'] = respond_bad
    shared['re_response']['help_re1'] = respond_help
    shared['re_response']['help_re2'] = respond_help


def setup_commands(all_commands: dict):
    pass

