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
from irctools import require_auth, CLR_HGLT, CLR_RESET
import ircpacket as ircp

_IS_TRACING = False
try:
    import tracemalloc  # pylint: disable=wrong-import-order,wrong-import-position
    if tracemalloc.is_tracing():
        _IS_TRACING = True
except ImportError:
    pass

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


def stats_command(__: tuple, packet: ircp.Packet, shared: dict):
    """ Print statistical data about this bot """
    stats = shared['stats']
    uptime = _uptime(shared['stats']['starttime'])

    import resource
    mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    tracing_status = (lambda x: 'enabled' if x else 'disabled')(_IS_TRACING)
    from platform import platform, python_version

    output = (packet.notice('Current uptime: {}'.format(uptime)),
              packet.notice('Available plugins: {}'.format(stats['plugins.available'])),
              packet.notice('Disabled plugins: {}'.format(stats['plugins.disabled'])),
              packet.notice('Failed plugins: {}'.format(stats['plugins.failed'])),
              packet.notice('Parsed messages: {}'.format(stats['num_messages'])),
              packet.notice('Commands run: {}'.format(stats['commands_run'])),
              packet.notice('Regex Matches: {}'.format(stats['regex_matches'])),
              packet.notice('Probot memory usage: {} KB'.format(mem_usage)),
              packet.notice('Bot admins online: {}'.format(len(shared['auth']))),
              packet.notice('Memory tracing is {}'.format(tracing_status)),
              packet.notice('Cows: {}:moo{}'.format(CLR_HGLT, CLR_RESET)),
              packet.notice('Platform: {}'.format(platform())),
              packet.notice('Running on Python {}'.format(python_version())))

    return output


def uptime_command(__: tuple, packet: ircp.Packet, shared: dict):
    """ Print current uptime """
    start_time = shared['stats']['starttime']
    uptime = _uptime(start_time)

    return packet.reply(uptime)


@require_auth
def memory_command(args: tuple, packet: ircp.Packet, ___: dict):
    """ Print the biggest memory hogs """
    if not _IS_TRACING:
        return packet.notice('Sorry, but tracing is currently disabled. '
                             'Please restart probot with the "PYTHONTRACEMALLOC=NFRAME" '
                             'environment variable.')

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('filename')

    num = 15
    if len(args) >= 2:
        try:
            num = int(args[1])
        except ValueError:
            num = 15

    output = [packet.notice('Top {} biggest memory hogs:'.format(num))]
    for num, stat in enumerate(top_stats[:num]):
        output.append(packet.notice('{}: {}'.format(num, stat)))

    return output


@require_auth
def memory_obj(args: tuple, packet: ircp.Packet, ___: dict):
    """ Print the biggest memory hogs """
    if not _IS_TRACING:
        return packet.notice('Sorry, but tracing is currently disabled. '
                             'Please restart probot with the "PYTHONTRACEMALLOC=NFRAME" '
                             'environment variable.')

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('filename')

    num = 0
    if len(args) >= 2:
        try:
            num = int(args[1])
        except ValueError:
            return packet.notice('Your argument must be an integer')
    else:
        return packet.notice('You must specify an object to inspect!')

    if len(top_stats) >= num:
        output = [packet.notice('Memory hog #{}'.format(num))]
        obj = top_stats[num]
        trace = tracemalloc.get_object_traceback(obj)
        for line in trace:
            output.append(packet.notice(line))
        return output
    else:
        return packet.notice('Sorry, but that object does not exist')


def setup_resources(config: dict, shared: dict):
    shared['help']['stats'] = 'Get simple statistics about this bot (admins only) || :stats'
    shared['help']['memory'] = 'Find the biggest memory hogs (admins only) || :memory [num]'
    shared['help']['memory-obj'] = 'Find the biggest memory hogs (admins only) || :memory-obj <num>'
    shared['help']['uptime'] = 'Get the current uptime for this bot || :uptime'

    shared['cooldown']['stats'] = 10
    shared['cooldown']['uptime'] = 3
    shared['cooldown']['memory'] = 3
    shared['cooldown']['memory-obj'] = 3


def setup_commands(all_commands: dict):
    com = all_commands

    com['stats'] = stats_command
    com['uptime'] = uptime_command
    com['memory'] = memory_command
    com['memory-obj'] = memory_obj
