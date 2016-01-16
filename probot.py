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


import socket
import logging
import time
import os
import json
import logging
import time
import os
import irc_argparse
from collections import deque
import pkgutil
import asynchat
import asyncore
from traceback import format_exc
from types import GeneratorType
from sys import stdout, version_info

# In Python 3.4+ imp is depreciated in favor of the easier
# `importlib`. This block detects if importlib is available,
# and falls back to `imp` when not available.
if version_info >= (3, 4):
    from importlib import import_module, reload
else:
    from imp import find_module, load_module

import ircpacket as ircp
import plugins
from irctools import CLR_HGLT, CLR_NICK, CLR_RESET, require_auth

# Make sure we don't send spam when send do smilies
from string import ascii_lowercase
ALLOWABLE_START_CHARS = set(ascii_lowercase)
BAD_START_CHARS = {'d', 'p', 'o'}
for c in BAD_START_CHARS:
    ALLOWABLE_START_CHARS.remove(c)

all_plugins = set()      # All plugins as string
plugin_list = set()      # Loaded plugins as modules
disabled_plugins = set() # Disabled plugins (strings)
failed_plugins = set()   # Plugins which failed to load (strings)

# Color codes constants for mIRC
CLR_HGLT = '3'
CLR_RESET = ''
CLR_NICK = '11'
VERSION = '0.9'
FORMATTING = 'UTF-8'

STOP = 0
RESTART = 1


def is_iterable(obj):
    ''' Figure out if an object is iterable '''
    return type(obj) == list or type(obj) == tuple or \
            type(obj) == GeneratorType or type(obj) == set

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
        print('DEBUG OUT: {}'.format(text))
        self.push(bytes('{}\r\n'.format(text), FORMATTING))

    def handle_connect(self): 
        ''' Responsible for inital connection to the
        IRC server, as well as setting our nickname
        '''
        self.write('NICK {}'.format(self.nick))
        self.write('USER {0} {0} {0} :An IRC Bot created by linuxtinkerer'.format(self.nick))
        #self.write(('USER', self.uid, '+iw', self.nick), self.name)


    def collect_incoming_data(self, data: str): 
        self.ibuffer += data

    def found_terminator(self): 
        line_bytes = self.ibuffer
        self.ibuffer = bytes()

        line = line_bytes.decode(encoding=FORMATTING)
        print('DEBUG  IN: {}'.format(line))
        #pipe_main.send(line)

        reply = handle_incoming(line, self.shared_data)
        if reply == None:
            return

        if type(reply) == str:
            self.write(reply)
        elif is_iterable(reply):
            for message in reply:
                if type(message) == str:
                    self.write(message)
                elif type(message) == int:
                    self.handlequit(message)

    def handlequit(self, flag):
        ''' Method to handle restarts and shutdowns
        '''
        if flag == STOP:
            self.close()
        elif flag == RESTART:
            self.restart= True
            self.close()
        else:
            print('Don\'t know what to do with flag value {}'.format(flage))
            print('So I\'m just gonna quit')
            self.close()


    def run(self, host, port): 
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
        except Exception as e:
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
    com['plugins'] = plugin_info_command
    com['auth'] = auth_command
    com['disable'] = plugin_toggle
    com['enable'] = plugin_toggle

    shared['help']['stop'] = 'Stop this bot and make it quit (admins only) || :stop'
    shared['help']['restart'] = 'Stop this bot and make it restart (admins only) || :restart'
    shared['help']['reload'] = 'Reload this bot\'s plugins || :reload'
    shared['help']['plugin'] = 'Get information about a plugin || :plugin <plugin> || :plugin wikipedia'
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
    #print(os.path.join(shared['dir'], 'plugins'))
    # We don't clear disabled_plugins because it's just strings that persist
    # between `reloads and restarts
    all_plugins.clear()
    plugin_list.clear()
    failed_plugins.clear()

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
        #>>> plugs = imp.load_module('plugins', pf, '{}/plugins/__init__.py'.format(os.getcwd()), ('.py', 'r', 1))
        pl_path = '{}/plugins/__init__.py'.format(os.getcwd())
        print('looking in {}'.format(pl_path))
        pf = open(pl_path, 'r')
        pl = load_module('plugins', pf, pl_path, desc)
        #pl = load_module('plugins', fp, pathname, desc)

    all_plugins.clear()
    # if no modules already enabled
    for importer, modname, ispkg in pkgutil.iter_modules([os.path.join(shared['dir'], 'plugins')]):
        all_plugins.add(modname)

    for modname in all_plugins:
        print('importing {}'.format(modname))
        all_plugins.add(modname)
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
                pf = open(pl_path, 'r')
                module = load_module(pl_name, pf, pl_path, desc)

            print('Loaded {}'.format(module))
            # Plugins without __plugin_enabled__ are never loaded.
            if '__plugin_enabled__' in dir(module):
                plugin_list.add(module)

                if module.__plugin_enabled__:
                    continue

                disabled_plugins.add(modname)
            else:
                print('I found a plugin called "{}" that I didn\'t load.'.format(modname))
                raise ImportError('No __plugin_enabled__ :(')
        except ImportError as e:
            print('Couldn\'t load {}'.format(modname))
            print('Exception: {}'.format(e))
            disabled_plugins.add(modname)
            failed_plugins.add(modname)

    # TODO: Gracefully handle plugin setup fail
    for p in plugin_list:
        short_name = p.__name__.lstrip('plugins.')
        if short_name not in disabled_plugins:
            print('setting up {}'.format(p))
            p.setup_resources(shared['conf'], shared)
            p.setup_commands(shared['commands'])


@require_auth
def reload_command(arg: tuple, packet: ircp.Packet, shared: dict):
    '''
    Reloads all plugins as well as their data files
    '''
    print('Reload command called')
    load_plugins(shared)

    if len(failed_plugins) + len(disabled_plugins) == 0:
        return packet.notice('All {} plugins reloaded!'.format(len(plugin_list)))

    response = [packet.notice('{} plugins were reloaded.'.format(len(plugin_list))),
                packet.notice('The following were NOT loaded: ')]

    if len(failed_plugins) > 0:
        response.append(packet.notice('Fail to Load:  ' + ', '.join(failed_plugins)))
    if len(disabled_plugins) > 0:
        response.append(packet.notice('Disabled: '  + ', '.join(disabled_plugins)))

    response.append(packet.notice('Please check your logs for further information.'))

    return response


@require_auth
def stop_command(arg: list, packet: ircp.Packet, shared: dict):
    '''
    Stops this bot
    '''
    import logging
    from plugins.internal import write_to_log

    if arg[0].lower() == 'stop':
        logging.info('Stop command received; stopping bot.')
        return STOP
    elif arg[0].lower() == 'restart':
        logging.info('Restart command received; stopping bot.')
        return RESTART
    else:
        print('wtf just happened here?')

    #write_to_log('User {0} tried to run `stop` command.'.format(packet.sender))
    #return_msg = ('STOP TRYING TO BREAK THIS BOT, ASSHOLE. THIS INCIDENT '
    #              'WILL BE REPORTED TO SANTA CLAUS, ANONYMOOSE, THE '
    #              'HACKER 4CHAN, TEH FBI, THE CIA, AND THE NSA!!!111!!one!1')
    #return ircp.make_notice(return_msg, packet.sender)


@require_auth
def plugin_info_command(arg: tuple, packet: ircp.Packet, shared: dict):
    '''
    Does stuff to plugins
    '''
    comm = arg[0].lower()
    config = shared['conf']
    global disabled_plugins

    if comm == 'plugins':
        enabled = all_plugins.difference(disabled_plugins).difference(failed_plugins)

        output = [packet.notice('Enabled plugins ({}): '.format(len(enabled))),
                  packet.notice(', '.join(enabled))]
        if len(disabled_plugins) > 0:
            output.append(packet.notice('Disabled plugins ({})'.format(len(disabled_plugins))))
            output.append(packet.notice(', '.join(disabled_plugins)))

        return output

    elif comm == 'plugin':
        if len(arg) < 2:
            return packet.notice('You need to specify a plugin to inspect!')

        name = arg[1].lower()

        if name not in all_plugins:
            return packet.notice('{} is not a valid plugin name'.format(name))

        #is_enabled = (name in enabled)
        is_enabled = not (name in disabled_plugins or name in failed_plugins)

        module = None
        full_name = 'plugins.{}'.format(name)
        for p in plugin_list:
            if p.__name__ == full_name:
                module = p
                break

        output = []
        output.append(packet.notice('{} is {}'.format(name, (lambda x: 'ENABLED' if True else 'DISABLED')(is_enabled))))
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
    else:
        print('You dun\' goofed.')


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
        if not (name in disabled_plugins or name in failed_plugins):
            return packet.notice('Plugin is already enabled. Doing nothing.')

        if name in disabled_plugins:
            disabled_plugins.remove(name)
        if name in failed_plugins:
            failed_plugins.remove(name)

        return packet.notice('Plugin is now enabled.')
    elif command == 'disable':
        if name in disabled_plugins:
            return packet.notice('Plugin is already disabled!')
        else:
            disabled_plugins.add(name)
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



def load_textfile(filename):
    """Loads multiline message form a text file into a tuple"""
    with open(filename) as f:  # Pythonic
        return tuple(line.strip() for line in f)


def json_save(filename, dump_dict):
    """
    Saves a dictionary to a JSON file

    filename - string of filename to write dump_dict to
    dump_dict - dictionary object to save
    """
    logging.info('saving file')
    with open(filename, 'wt') as f:
        # We indent so it's human readable. Sort for easy offline editing
        json.dump(dump_dict, f, indent=True, sort_keys=True)
        logging.info('file saved')


def load_json(filename):
    """Load and parse a JSON file"""
    filestring = ''

    with open(filename) as jsfile:
        for line in jsfile:
            filestring += line

    json_dict = json.loads(filestring)
    return json_dict


def get_cooldown(c: str, now: float, shared: dict):
    ''' Get the time that a user should be off of their
    cooldown for using a command

    c - the command
    now - the current (unix) time (in seconds)
    shared - shared data dictionary
    '''
    cool = now

    if c in shared['cooldown']:
        value = shared['cooldown'][c]

        # Handle aliases
        if type(value) == str:
            value = shared['cooldown'][value]

        return cool + value
    else:
        # Default cooldown is 5 seconds
        return cool +  5


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


    info_str = 'probot version {0}. My owner is {2}{1}{3}.'.format(VERSION, config['admin'], CLR_NICK, CLR_RESET)
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
        'recent_messages': deque(maxlen=30)
    }

    # load plugins. This *has* to happend *after* shared_data is set up
    a = load_plugins(shared_data)
    print('plugins: {}'.format(plugin_list))

    # TODO: Keep list of last 30 packets and the channels they are from
    return shared_data


def handle_incoming(line, shared_data):
    ''' Handles, and replies to incoming IRC messages

    line - the line to parse
    shared_data - the shared_data with literally everything in it
    '''
    reply = None        # Reset reply
    msg_packet = None

    msg_packet = ircp.Packet(line)

    # Determine if prefix is at beginning of message
    # If it is, then parse for commands
    if msg_packet.msg_type == 'PRIVMSG':
        # Do we need to parse mess? If so, parse it
        msg_text = msg_packet.text
        if len(msg_text) > 1 and msg_text[0] == config['prefix']:  # If message starts with prefix
            now = time.time()
            if (msg_packet.sender not in shared_data['cooldown_user']) or \
                (now > shared_data['cooldown_user'][msg_packet.sender]):
                stripped_text = msg_text[1:]
                words = irc_argparse.parse(stripped_text)
                if (words[0] != ''):
                    c = words[0].lower()
                    commands = shared_data['commands']
                    if c in commands:
                        #print('command: {}'.format(c))
                        reply = commands[c](words, msg_packet, shared_data)
                        #print('reply: {}'.format(reply))

                        cool = get_cooldown(c, now, shared_data)
                        shared_data['cooldown_user'][msg_packet.sender] = cool
                    elif c[0] in ALLOWABLE_START_CHARS:
                        # make sure that we don't respond to a smily
                        reply = ircp.make_notice('Sorry, but that command does not exist.', msg_packet.sender)
            else:
                time_left = (shared_data['cooldown_user'][msg_packet.sender] - int(now))
                reply = msg_packet.reply(('You need to wait. '
                    'Your cooldown ends in {:.1f} seconds').format(time_left))
        else:
            for re_name in shared_data['regexes']:
                regex = shared_data['regexes'][re_name]
                match = regex.search(msg_packet.text)
                if match != None:
                    print('matched to regex "{}"'.format(re_name))
                    reply = shared_data['re_response'][re_name](match, msg_packet, shared_data)
                    break
    #elif (not shared_data['conf']['logged_in']) and msg_packet.msg_type == 'NUMERIC':
    #    if msg_packet.numeric == ircp.Packet.numerics['RPL_ENDOFMOTD']:  # When first logging in
    #        reply = ircp.make_message('identify {}'.format(config['password']), 'NickServ')
    #        reply = []
    #        for channel in config['channels'].split(' '):
    #            if config['intro']:
    #                j, r = ircp.join_chan(channel, config['intro'])
    #                reply.extend((j, r))
    #            else:
    #                reply.append(ircp.join_chan(channel))
    #            print('Joining channel {}'.format(channel))
    #            shared_data['chan'].append(channel)
    #        shared_data['conf']['logged_in'] = True  # Stop checking for login numerics

    elif msg_packet.msg_type == 'NUMERIC':
        if msg_packet.numeric == ircp.Packet.numerics['RPL_ENDOFMOTD']:
            reply = (ircp.join_chan(c) for c in shared['conf']['channels'].split(' '))
            #shared_data['chan'].extend(c for c in shared['conf']['channels'].split(' '))
    elif msg_packet.msg_type == 'PING':
        reply = 'PONG {}'.format(msg_packet.host)

    elif msg_packet.msg_type == 'NICK':
        print('{} changed nick to {}'.format(msg_packet.sender, msg_packet.nick_to))
        if msg_packet.sender in shared['auth']:
            shared['auth'].remove(msg_packet.sender)
            shared['auth'].add(msg_packet.nick_to)
            print('moved {} to {} on auth list'.format(msg_packet.sender, msg_packet.nick_to))

    elif msg_packet.msg_type in ('PART', 'QUIT'):
        if msg_packet.sender in shared['auth']:
            shared['auth'].remove(msg_packet.sender)
            print('removed {} from auth list'.format(msg_packet.sender))

    elif msg_packet.msg_type == 'JOIN':
        if msg_packet.sender == shared['conf']['bot_nick']:
            shared['chan'].add(msg_packet.target)
            reply = ircp.make_message(shared['conf']['intro'], msg_packet.target)
    else:
        pass

    if (type(reply) == int):
        flag = int(reply)
        reply = [ircp.make_message('kthxbai', c) for c in shared_data['chan']]
        reply.append(flag) # Makes sure to close out.

    shared_data['recent_messages'].append(msg_packet)

    return reply

# Stuff to run on startup
if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(filename='probot.log', level=logging.DEBUG)

    # Load configuration file
    logging.info('Loading configuration (main)')
    config = load_json('config.json')

    server = config['address']
    port = int(config['port'])
    bot_nick = config['nick']
    admin = config['admin']
    # Do we try to encrypt?
    #use_tls = (lambda x: x[0].lower() == 'y')(config['encrypt'])
    intro = config['intro']
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
