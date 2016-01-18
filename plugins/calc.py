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


import math
import ircpacket as ircp

__plugin_description__ = 'Simple command-line calculator'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'command'
__plugin_enabled__ = True

sqrt = math.sqrt
r = math.sqrt
s = math.sin
c = math.cos
t = math.tan
p = math.pi

ALLOWED = set('( ) 0 1 2 3 4 5 6 7 8 9 - = + / * // . % r q s c t p e'.split(' '))
ALLOWED.add(' ')


def evaluate_expression(expression: str) -> int:
    ''' Evaluate a mathematical expression

    eval() is used here, so we make sure to toss out anything
    that could be potentially unsafe for us to take from a random
    stranger on IRC.


    '''
    for char in expression:
        if char not in ALLOWED:
            print('{} is not allowed'.format(char))
            return

    try:
        print(expression)

        val = eval(expression)  # pylint: disable=eval-used
        return val
    except Exception as e:
        print(e)
        raise e


def calc_command(arg: tuple, packet: ircp.Packet, shared: dict) -> str:
    ''' Evaluate a mathematical expression

    usage:
    :calc <expression>
    :calc 1 + 1 == 2
    :calc 3^3
    '''
    problem = (''.join(arg[1:])).replace('^', '**')
    print('solving for {}'.format(problem))
    try:
        result = evaluate_expression(problem)
        if result is None:
            raise ValueError('Invalid result')

        reply = 'Result: {}'.format(result)
        return packet.reply(reply)
    except ZeroDivisionError as e:
        return packet.notice('Error: Divide by zero.')
    except Exception as e:
        print(e)
        return packet.notice('Sorry, but that expression was invalid. Please try again.')


def setup_resources(config: dict, shared: dict):
    shared['help']['calc'] = 'Evaluate a math problem || :calc <expression> || :calc 3.14 ^ 2 + 2'
    shared['cooldown']['calc'] = 1


def setup_commands(all_commands: dict):
    all_commands['calc'] = calc_command
