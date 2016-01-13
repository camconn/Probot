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


__plugin_name__ = 'substitution'
__plugin_description__ = 'Simple substitution using s/old/new/'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'combined'
__plugin_enabled__ = False


REGEX_SUB ='^s/.*/.*\/g?$'

def sub_replace(old_message, sub_message):
    """
    Perform substitution regular expression on previous message.
    """

    _, old, new, g_flag = sub_message.split('/')

    if g_flag.lower() == 'g':
        return old_message.replace(old, new)
    else:
        return old_message.replace(old, new, 1)

def setup_resources(config: dict, shared: dict):
    pass

def setup_commands(all_commands: dict):
    pass
