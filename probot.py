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
Probot - A versatile IRC bot written in Python

This file is the business logic of the bot. Things such as
connection handling, parsing, and plugin loading are all done
here.

The latest version of this source code is at available at
https://github.com/camconn/probot
'''

import socket
import logging
import time
import os
from collections import deque
import pkgutil
import asynchat
import asyncore
from traceback import format_exc
from types import GeneratorType
from sys import stdout, version_info
from string import ascii_lowercase

# In Python 3.4+ imp is depreciated in favor of the easier
# `importlib`. This block detects if importlib is available,
# and falls back to `imp` when not available.
if version_info >= (3, 4):
    from importlib import import_module, reload
else:
    from imp import load_module

import ircpacket as ircp  # NOQA
from irctools import CLR_NICK, CLR_RESET, CLR_HGLT, require_auth, load_json  # NOQA
import plugins  # NOQA
import irc_argparse  # NOQA

# Make sure we don't send spam when send do smilies
ALLOWABLE_START_CHARS = set(ascii_lowercase)
BAD_START_CHARS = {'d', 'p', 'o'}
for ch in BAD_START_CHARS:
    ALLOWABLE_START_CHARS.remove(ch)

ALL_PLUGINS = set()       # All plugins as string
PLUGIN_LIST = set()       # Loaded plugins as modules
DISABLED_PLUGINS = set()  # Disabled plugins (strings)
FAILED_PLUGINS = set()    # Plugins which failed to load (strings)

# Color codes constants for mIRC
VERSION = '0.9'
FORMATTING = 'UTF-8'

STOP = 0
RESTART = 1


def is_iterable(obj):
    ''' Figure out if an object is iterable '''
    return (isinstance(obj, list) or isinstance(obj, tuple) or
            isinstance(obj, GeneratorType) or isinstance(obj, set))


class IRCClient(asynchat.async_chat):
    ''' Asyncronous IRC client that handles chat, networking IO,
    and everything else that goes along with that.
    '''
    def __init__(self, nick, shared_data):
        asynchat.async_chat.__init__(self)
        self.ibuffer = bytes()
        self.set_terminator(bytes('\r\n', FORMATTING))
        self.nick = nick
        self.shared_data = shared_data
        self.restart = False

    def write(self, text):
        ''' Write some text to the open socket '''
        print('DEBUG OUT: {}'.format(text))
        self.push(bytes('{}\r\n'.format(text), FORMATTING))

    def handle_connect(self):
        ''' Responsible for inital connection to the
        IRC server, as well as setting our nickname
        '''
        self.write('NICK {}'.format(self.nick))
        self.write('USER {0} {0} {0} :The best IRC bot around'.format(self.nick))

    def collect_incoming_data(self, data: str):
        self.ibuffer += data

    def found_terminator(self):
        line_bytes = self.ibuffer
        self.ibuffer = bytes()

        line = line_bytes.decode(encoding=FORMATTING)
        print('DEBUG  IN: {}'.format(line))

        reply = handle_incoming(line, self.shared_data)
        if reply is None:
            return

        if isinstance(reply, str):
            self.write(reply)
        elif is_iterable(reply):
            for message in reply:
                if isinstance(message, str):
                    self.write(message)
                elif isinstance(message, int):
                    self.handlequit(message)

    def handlequit(self, flag):
        ''' Method to handle restarts and shutdowns
        '''
        if flag == STOP:
            self.close()
        elif flag == RESTART:
            self.restart = True
            self.close()
        else:
            print('Don\'t know what to do with flag value {}'.format(flag))
            print('So I\'m just gonna quit')
            self.close()

    def run(self, host, port):
        ''' Run the client targeted at a host on a port '''
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(0.15)
        self.connect((host, port))
        time.sleep(0.1)
        asyncore.loop(65)
        return self.restart

    def handle_error(self):
        ''' We handle the error here so that we don't
        disconnect from the server. After all, uptime is
        the #1 priority!
        '''
        trace = format_exc()
        try:
            print(trace)
            logging.debug('An error occurred...\nHere\'s the traceback:')
            logging.debug(trace)
        except Exception:
            print('An error broke loose!')


def load_builtins(shared: dict):
    ''' Small set of internal commands used to maintain state.
    This *CANNOT* crash, so it's maintained internally. This
    is not allowed fail loading, or be reloaded.
    '''
    com = shared['commands']

    com['stop'] = stop_command
    com['restart'] = stop_command
    com['reload'] = reload_command
    com['plugin'] = plugin_info_command
    com['plugins'] = list_plugins
    com['auth'] = auth_command
    com['disable'] = plugin_toggle
    com['enable'] = plugin_toggle

    shared['help']['stop'] = 'Stop this bot and make it quit (admins only) || :stop'
    shared['help']['restart'] = 'Stop this bot and make it restart (admins only) || :restart'
    shared['help']['reload'] = 'Reload this bot\'s plugins || :reload'
    shared['help']['plugin'] = ('Get information about a plugin '
                                '|| :plugin <plugin> || :plugin wikipedia')
    shared['help']['plugins'] = 'List all plugins available || :plugins'
    shared['help']['auth'] = 'Authenticate yourself || :auth <password> || :auth hunter2'
    shared['help']['enable'] = 'Enable a plugin || :enable <plugin> || :enable rekt'
    shared['help']['disable'] = 'Disable a plugin || :disable <plugin> || :disable told'

    shared['cooldown']['stop'] = 5
    shared['cooldown']['restart'] = 5
    shared['cooldown']['reload'] = 3
    shared['cooldown']['plugin'] = 2
    shared['cooldown']['plugins'] = 5
    shared['cooldown']['auth'] = 1
    shared['cooldown']['enable'] = 1
    shared['cooldown']['disable'] = 1


def load_plugins(shared: dict):
    ''' (Re)Load all plugins for the bot

    This is a bug function, look into breaking it up into smaller things
    '''
    # print(os.path.join(shared['dir'], 'plugins'))
    # We don't clear DISABLED_PLUGINS because it's just strings that persist
    # between `reloads and restarts
    ALL_PLUGINS.clear()
    PLUGIN_LIST.clear()
    FAILED_PLUGINS.clear()

    shared['commands'].clear()
    shared['help'].clear()
    shared['regexes'].clear()
    shared['re_response'].clear()

    load_builtins(shared)

    desc = ('.py', 'r', 1)

    if version_info >= (3, 4):
        # Python 3.4+
        reload(plugins)
    else:
        # Python 3.2+
        pl_path = '{}/plugins/__init__.py'.format(os.getcwd())
        print('looking in {}'.format(pl_path))
        py_file = open(pl_path, 'r')
        # The below lines makes flake8 upset. Let's ignore it.
        load_module('plugins', py_file, pl_path, desc)  # NOQA

    ALL_PLUGINS.clear()
    # if no modules already enabled
    for importer, modname, ispkg in pkgutil.iter_modules([os.path.join(shared['dir'], 'plugins')]):  # pylint: disable=unused-variable
        ALL_PLUGINS.add(modname)

    for modname in ALL_PLUGINS:
        print('importing {}'.format(modname))
        ALL_PLUGINS.add(modname)
        try:
            module = None

            if version_info >= (3, 4):
                # Python 3.4+
                module = import_module('.' + modname, package='plugins')
                reload(module)
            else:
                # Python 3.2 - 3.3
                pl_path = '{}/plugins/{}.py'.format(os.getcwd(), modname)
                pl_name = 'plugins.{}'.format(modname)
                print('looking in {}'.format(pl_path))
                py_file = open(pl_path, 'r')
                module = load_module(pl_name, py_file, pl_path, desc)

            print('Loaded {}'.format(module))
            # Plugins without __plugin_enabled__ are never loaded.
            if '__plugin_enabled__' in dir(module):
                PLUGIN_LIST.add(module)

                if module.__plugin_enabled__:
                    continue

                DISABLED_PLUGINS.add(modname)
            else:
                print('I found a plugin called "{}" that I didn\'t load.'.format(modname))
                raise ImportError('No __plugin_enabled__ :(')

        except ImportError as error:
            print('Couldn\'t load {}'.format(modname))
            print('Exception: {}'.format(error))
            DISABLED_PLUGINS.add(modname)
            FAILED_PLUGINS.add(modname)

    # TODO: Gracefully handle plugin setup fail
    for plug in PLUGIN_LIST:
        short_name = plug.__name__.lstrip('plugins.')
        if short_name not in DISABLED_PLUGINS:
            print('setting up {}'.format(plug))
            plug.setup_resources(shared['conf'], shared)
            plug.setup_commands(shared['commands'])

    # Set up stats
    shared['stats']['plugins.available'] = len(ALL_PLUGINS)
    shared['stats']['plugins.disabled'] = len(DISABLED_PLUGINS)
    shared['stats']['plugins.failed'] = len(FAILED_PLUGINS)


@require_auth
def reload_command(_: tuple, packet: ircp.Packet, shared: dict):
    '''
    Reloads all plugins as well as their data files
    '''
    print('Reload command called')
    load_plugins(shared)
    if len(FAILED_PLUGINS) + len(DISABLED_PLUGINS) == 0:
        return packet.notice('All {} plugins reloaded!'.format(len(PLUGIN_LIST)))

    response = [packet.notice('{} plugins were reloaded.'.format(len(PLUGIN_LIST))),
                packet.notice('The following were NOT loaded: ')]

    if len(FAILED_PLUGINS) > 0:
        response.append(packet.notice('Fail to Load:  ' + ', '.join(FAILED_PLUGINS)))
    if len(DISABLED_PLUGINS) > 0:
        response.append(packet.notice('Disabled: ' + ', '.join(DISABLED_PLUGINS)))

    response.append(packet.notice('Please check your logs for further information.'))

    return response


@require_auth
def stop_command(arg: list, packet: ircp.Packet, shared: dict):
    '''
    Stops this bot
    '''
    if arg[0].lower() == 'stop':
        logging.info('Stop command received; stopping bot.')
        return STOP
    elif arg[0].lower() == 'restart':
        logging.info('Restart command received; stopping bot.')
        return RESTART
    else:
        print('wtf just happened here?')


@require_auth
def list_plugins(arg: tuple, packet: ircp.Packet, shared: dict):
    ''' List all plugins available

    :plugins
    '''
    enabled = ALL_PLUGINS.difference(DISABLED_PLUGINS).difference(FAILED_PLUGINS)

    output = [packet.notice('Enabled plugins ({}): '.format(len(enabled))),
              packet.notice(', '.join(enabled))]
    if len(DISABLED_PLUGINS) > 0:
        output.append(packet.notice('Disabled plugins ({})'.format(len(DISABLED_PLUGINS))))
        output.append(packet.notice(', '.join(DISABLED_PLUGINS)))

    return output


@require_auth
def plugin_info_command(arg: tuple, packet: ircp.Packet, shared: dict):
    '''
    Does stuff to plugins
    '''
    if len(arg) < 2:
        return packet.notice('You need to specify a plugin to inspect!')

    name = arg[1].lower()

    if name not in ALL_PLUGINS:
        return packet.notice('{} is not a valid plugin name'.format(name))

    is_enabled = not (name in DISABLED_PLUGINS or name in FAILED_PLUGINS)

    module = None
    full_name = 'plugins.{}'.format(name)
    for plug in PLUGIN_LIST:
        if plug.__name__ == full_name:
            module = plug
            break

    output = []
    enabled_text = (lambda x: 'ENABLED' if x else 'DISABLED')(is_enabled)
    output.append(packet.notice('{} is {}'.format(name, enabled_text)))
    if module:
        if '__plugin_description__' in dir(module):
            output.append(packet.notice(module.__plugin_description__))
        if '__plugin_author__' in dir(module):
            output.append(packet.notice('Author: {}'.format(module.__plugin_author__)))
        if '__plugin_version__' in dir(module):
            output.append(packet.notice('Version: {}'.format(module.__plugin_version__)))
        if '__plugin_type__' in dir(module):
            output.append(packet.notice('Plugin Type: {}'.format(module.__plugin_type__)))

    return output


@require_auth
def plugin_toggle(arg: tuple, packet: ircp.Packet, shared: dict):
    ''' Enable or disable plugins

    :enable <plugin>
    :disable <plugin>
    '''
    if len(arg) < 2:
        return packet.notice('You need to specify a plugin to disable')
    if len(arg) > 2:
        return packet.notice('Too many arguments! The command only uses 1 argument.')

    command = arg[0].lower()
    name = arg[1].lower()

    if command == 'enable':
        if not (name in DISABLED_PLUGINS or name in FAILED_PLUGINS):
            return packet.notice('Plugin is already enabled. Doing nothing.')

        if name in DISABLED_PLUGINS:
            DISABLED_PLUGINS.remove(name)
        if name in FAILED_PLUGINS:
            FAILED_PLUGINS.remove(name)

        return packet.notice('Plugin is now enabled.')
    elif command == 'disable':
        if name in DISABLED_PLUGINS:
            return packet.notice('Plugin is already disabled!')
        else:
            DISABLED_PLUGINS.add(name)
            # TODO: Reload plugins to get rid of leftovers
            return packet.notice('Plugin is now disabled!')
    else:
        print('You screwed up.')


# LOL, don't @require_auth here!
def auth_command(arg: tuple, packet: ircp.Packet, shared: dict):
    ''' Authenticate yourself

    :auth <password>
    '''
    if len(arg) < 2:
        return packet.notice('You must specify a password!')

    passphrase = arg[1]

    if passphrase == shared['conf']['adminpass']:
        if packet.sender in shared['auth']:
            return packet.notice('You are already logged in!')
        else:
            shared['auth'].add(packet.sender)
            print('{} successfully authenticated.'.format(packet.sender))
            return packet.notice('Authentication success!')
    else:
        return packet.notice('Authentication failure. Try again later.')


def get_cooldown(command: str, now: float, shared: dict):
    ''' Get the time that a user should be off of their
    cooldown for using a command

    c - the command
    now - the current (unix) time (in seconds)
    shared - shared data dictionary
    '''
    cool = now

    if command in shared['cooldown']:
        value = shared['cooldown'][command]

        # Handle aliases
        if isinstance(value, str):
            value = shared['cooldown'][value]

        return cool + value
    else:
        # Default cooldown is 5 seconds
        return cool + 5


def setup(config):
    """
    Main loop for second thread of program

    config - dictionary of configuration values for probot
    """
    m_config = config

    config = {
        'bot_nick': m_config['nick'],
        'channels': m_config['channels'],
        'password': m_config['password'],
        'logged_in': False,
        'active': True,
        'prefix': m_config['prefix'],
        'admin': m_config['admin'],
        'last_save': time.time(),
        'dict_update': False,
        'intro': m_config['intro'],
        'adminpass': m_config['adminpass'],
        'oxr_id': m_config['oxr_id'],
    }

    info_str = 'probot version {0}. My owner is {2}{1}{3}.'.format(
        VERSION, config['admin'], CLR_NICK, CLR_RESET)

    commands = dict()

    # This object acts as a form of persistent memory for the commands. This is particularly
    # useful for commands like `def` and `told`
    shared_data = {
        'conf': config,
        'info': info_str,
        'chan': set(),
        'dir': os.getcwd(),
        'commands': commands,
        'help': dict(),
        'regexes': dict(),
        're_response': dict(),
        'cooldown_user': dict(),
        'cooldown': dict(),
        'auth': set(),
        'recent_messages': deque(maxlen=30),
        'stats': dict(),
    }

    stats = shared_data['stats']
    stats['num_messages'] = 0
    stats['starttime'] = int(time.time())
    print('stats:')
    print(shared_data['stats'])

    # load plugins. This *has* to happend *after* shared_data is set up
    load_plugins(shared_data)
    print('plugins: {}'.format(PLUGIN_LIST))

    return shared_data


def handle_commands(packet: ircp.Packet, shared: dict):
    ''' Handle commands as needed '''
    if not (len(packet.text) > 1 and packet.text[0] == shared['conf']['prefix']):
        return None

    now = time.time()

    if (packet.sender not in shared['cooldown_user'] or
            now > shared['cooldown_user'][packet.sender]):
        stripped_text = packet.text[1:]
        words = irc_argparse.parse(stripped_text)
        if words[0] != '':
            c = words[0].lower()
            commands = shared['commands']
            if c in commands:
                cool = get_cooldown(c, now, shared)
                shared['cooldown_user'][packet.sender] = cool
                reply = commands[c](words, packet, shared)
                return reply
            elif c[0] in ALLOWABLE_START_CHARS:
                return packet.notice('Sorry, but the command {1}{0}{2} '
                                     'does not exist.'.format(c, CLR_HGLT, CLR_RESET))
    else:
        time_left = (shared['cooldown_user'][packet.sender] - int(now))
        return packet.notice('[Cooldown]: You need to wait for {:.1f} seconds '
                             'before you can use a command.'.format(time_left))


def handle_regexes(packet: ircp.Packet, shared: dict):
    ''' Handle regex matching and figuring out the output '''
    for re_name in shared['regexes']:
        regex = shared['regexes'][re_name]
        match = regex.search(packet.text)
        if match is not None:
            print('matched to regex "{}"'.format(re_name))
            return shared['re_response'][re_name](match, packet, shared)


def handle_incoming(line, shared_data):
    ''' Handles, and replies to incoming IRC messages

    line - the line to parse
    shared_data - the shared_data with literally everything in it
    '''
    config = shared_data['conf']
    reply = None  # Reset reply
    msg_packet = ircp.Packet(line)

    # Determine if prefix is at beginning of message
    # If it is, then parse for commands
    if msg_packet.msg_type == 'PRIVMSG':
        reply = handle_commands(msg_packet, shared_data)
        if reply is None:
            reply = handle_regexes(msg_packet, shared_data)
    elif msg_packet.msg_type == 'NUMERIC':
        if (config['password'] and not config['logged_in'] and
                msg_packet.numeric == ircp.Packet.numerics['RPL_ENDOFMOTD']):
            reply = []  # pylint: disable=redefined-variable-type
            reply.append(ircp.make_message('identify {} {}'.format(config['bot_nick'],
                                                                   config['password']),
                                           'nickserv'))
            for channel in config['channels'].split(' '):
                reply.append(ircp.join_chan(channel))
            shared_data['conf']['logged_in'] = True  # Stop checking for login numerics
        elif msg_packet.numeric == ircp.Packet.numerics['RPL_ENDOFMOTD']:
            reply = (ircp.join_chan(c) for c in shared_data['conf']['channels'].split(' '))

    elif msg_packet.msg_type == 'PING':
        reply = 'PONG {}'.format(msg_packet.host)

    elif msg_packet.msg_type == 'NICK':
        print('{} changed nick to {}'.format(msg_packet.sender, msg_packet.nick_to))
        if msg_packet.sender in shared_data['auth']:
            shared_data['auth'].remove(msg_packet.sender)
            shared_data['auth'].add(msg_packet.nick_to)
            print('moved {} to {} on auth list'.format(msg_packet.sender, msg_packet.nick_to))

    elif msg_packet.msg_type in ('PART', 'QUIT'):
        if msg_packet.sender in shared_data['auth']:
            shared_data['auth'].remove(msg_packet.sender)
            print('removed {} from auth list'.format(msg_packet.sender))

    elif msg_packet.msg_type == 'JOIN':
        if msg_packet.sender == shared_data['conf']['bot_nick']:
            shared_data['chan'].add(msg_packet.target)
            reply = ircp.make_message(shared_data['conf']['intro'], msg_packet.target)

    if isinstance(reply, int):
        flag = int(reply)
        reply = [ircp.make_message('kthxbai', c) for c in shared_data['chan']]
        reply.append(flag)  # Makes sure to close out.

    shared_data['recent_messages'].append(msg_packet)
    shared_data['stats']['num_messages'] += 1

    return reply


def main():
    ''' Start up the client and whatnot.
    This is what is run when executing the bot.
    '''
    # Setup logging
    logging.basicConfig(filename='probot.log', level=logging.DEBUG)

    # Load configuration file
    logging.info('Loading configuration (main)')
    config = load_json('config.json')

    server = config['address']
    port = int(config['port'])
    bot_nick = config['nick']
    logging.info('Loaded config (main)')

    shared = setup(config)

    # Create second thread
    client = IRCClient(bot_nick, shared)
    restart = client.run(server, port)

    if restart:
        print('restarting')
        stdout.flush()
        os.execl('./probot.py', '')

    # Do any needed tying of loose ends
    # Wait for other thread to stop then close pipe
    logging.info('Shutting down m8')

    # Shutdown socket gracefully
    print('Socket closed; bye!')


if __name__ == '__main__':
    main()
