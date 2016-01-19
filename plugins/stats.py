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


"""
Statistical information

Give statistical information about this bot (such as the number
of messages parsed)
"""


import datetime
from irctools import require_auth
import ircpacket as ircp


__plugin_description__ = 'Stats about this bot'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'command'
__plugin_enabled__ = True


def _uptime(start_time: int) -> str:
    ''' Get the current uptime as a string

    start_time - the Unix time this bot was started
    '''
    started = datetime.datetime.utcfromtimestamp(start_time)
    now = datetime.datetime.utcnow()

    uptime = now - started
    print(uptime.seconds)

    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)

    time_str = ''

    if uptime.days >= 2:
        time_str = '{} days, '.format(uptime.days)
    elif uptime.days == 1:
        time_str = '1 day, '

    if hours >= 2 or hours == 0:
        time_str = '{}{} hours, '.format(time_str, hours)
    elif hours == 1:
        time_str = '{}{} hour, '.format(time_str, hours)

    if minutes >= 2 or minutes == 0:
        time_str = '{}{} minutes, and '.format(time_str, minutes)
    else:
        time_str = '{}{} minute, and '.format(time_str, minutes)

    if seconds >= 2 or seconds == 0:
        time_str = '{}{} seconds.'.format(time_str, seconds)
    else:
        time_str = '{}{} second.'.format(time_str, seconds)

    return time_str


@require_auth
def stats_command(_: tuple, packet: ircp.Packet, shared: dict):
    """ Print statistical data about this bot """
    stats = shared['stats']
    uptime = _uptime(shared['stats']['starttime'])

    output = [packet.notice('Current uptime: {}'.format(uptime)),
              packet.notice('Available plugins: {}'.format(stats['plugins.available'])),
              packet.notice('Disabled plugins: {}'.format(stats['plugins.disabled'])),
              packet.notice('Failed plugins: {}'.format(stats['plugins.failed'])),
              packet.notice('Parsed messages: {}'.format(stats['num_messages']))]

    import resource
    mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    output.append(packet.notice('Memory usage: {} KB'.format(mem_usage)))

    return output


def uptime_command(_: tuple, packet: ircp.Packet, shared: dict):
    """ Print current uptime """
    start_time = shared['stats']['starttime']
    uptime = _uptime(start_time)

    return packet.reply(uptime)


def setup_resources(config: dict, shared: dict):
    shared['help']['stats'] = 'Get simple statistics about this bot (admins only) || :stats'
    shared['help']['uptime'] = 'Get the current uptime for this bot || :uptime'

    shared['cooldown']['stats'] = 3
    shared['cooldown']['uptime'] = 3


def setup_commands(all_commands: dict):
    com = all_commands

    com['stats'] = stats_command
    com['uptime'] = uptime_command
