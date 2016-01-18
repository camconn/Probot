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
IRCTools - Some syntactical sugar for plugin developers.

This file contains constants, decorators, and functions that
make the life of probot plugin developers easier.
'''

import ircpacket as ircp


# IRC Color Formatting Constants
CLR_RESET = ''                 # Formatting reset character
CLR_HGLT = '3'                 # Highlighting for commands
CLR_NICK = '11'                # Highlighting for nicks
CLR_ITLCS = chr(int("0x1d", 0))  # Italics formatting character


def require_auth(callback):
    ''' Decorator to make it easier for plugins to require authentication
    and restrict usage to bot admins.

    usage:
    @require_auth
    def my_fun_command(args: tuple, packet: ircpacket.Packet, shared: dict)
        return packet.reply('You are an admin!')
    '''
    def restricted_method(args: tuple, packet: ircp.Packet, shared: dict):  # pylint: disable=missing-docstring
        if packet.sender in shared['auth']:
            return callback(args, packet, shared)
        else:
            return packet.notice('You must be an admin to run this command. '
                                 'Please login first with :auth')
        return None
    return restricted_method


def require_public(callback):
    ''' Decorator to require that messages be sent to public chat before
    a command is executed at all.

    usage:
    @require_public
    def my_public_command(args: tuple, packet: ircpacket.Packet, shared: dict)
        return packet.reply('This was a public command!')
    '''
    def public_method(args: tuple, packet: ircp.Packet, shared: dict):  # pylint: disable=missing-docstring
        if packet.msg_public:
            return callback(args, packet, shared)
        else:
            return packet.notice('Sorry, but that command is only available '
                                 'through public chat. Try again in a public channel.')
        return None

    return public_method
