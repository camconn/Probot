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



# ===== PLUGIN METADATA README =====
# Adapt the below plugin metadata and change __plugin_enabled__ to True.
# If you don't change __plugin_enabled__ to true, your plugin will NOT
# be loaded.

# You should also make a copy of this file, and rename your version
# something like `myplugin.py`. You should keep this template for reference
# in case you'd like to make future plugins.

# You should also edit __plugin_type__ to something appropriate. This has no
# functional change to your program, but it helps your users out.
# As for __plugin_type__:
#     `command` - This plugin provides commands only.
#     `regex` - This plugin looks for regex patterns, and does something
#               whenever those are found (DON'T USE THIS FOR COMMANDS, YOU'RE
#               JUST HURTING YOURSELF!)
#     `both`  - This plugin uses both regexes as well as commands.

__plugin_description__ = 'Template example plugin'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'command'
__plugin_enabled__ = False


from os import path
import logging
import ircpacket as ircp
# IRC color codes that come in handy
from irctools import CLR_NICK, CLR_HGLT, CLR_RESET, CLR_ITLCS


def hello_world(arg: tuple, packet: ircp.Packet, shared: dict):
    ''' Hello, world!

    This is an example template command

    arg - the tuple of keywords
    packet - the packet object to receive
    shared - the shared data dictionary
    '''

    # arg[0] is always the command name (in this case 'hello', or 'h').
    # You can use this to assign multiple commands to the same function.
    # Different indexes are parsed similarly to how sys.argv is parsed,
    # paying attention to quotes and backslash-escapes.
    print(arg)

    return packet.reply('Hello, there!')


def setup_resources(config: dict, shared: dict):
    ''' Function to set up data, read configuration, as well
    as create help and cooldown entries.
    '''
    # You are responsible for setting up your help messages here.
    # Help definitions go in shared['help']. This is just a dict
    shared['help']['hello'] = 'Hello, world! || :hello'
    shared['help']['h'] = 'Alias for :hello'

    # For cooldowns, make your master command have a cooldown.
    # For aliases, you can assign them a string of the longer
    # command, to avoid duplicating cooldown times.
    shared['cooldown']['hello'] = 4
    shared['cooldown']['h'] = 'hello'

def setup_commands(all_commands: dict):
    ''' Function to assign commands to functions.
    '''
    # You can check to make sure you don't overwrite commands if you
    # are unsure if you are overwriting anybody else.
    all_commands['hello'] = hello_world
    all_commands['h'] = hello_world
