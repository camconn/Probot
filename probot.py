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
import re
import time
import os
import irc_argparse
#from collections import deque
from importlib import import_module, reload
import pkgutil
import asyncore
import asynchat
import re

import ircpacket as ircp
import builtin_commands as b

import plugins
#print('plugin path: {}'.format(plugins.__path__))
plugin_list = []
disabled = []

from string import ascii_lowercase

ALLOWABLE_START_CHARS = ascii_lowercase.replace('d', '').replace('p', '')

# Color codes constants for mIRC
CLR_HGLT = '3'
CLR_RESET = ''
CLR_NICK = '11'
VERSION = '0.9'

SMILIES = (':)',
           ':d',
           ':p',
           ':^')

# Global variables (I know this is bad, but they are staying here for now)
formatting = 'UTF-8'  # format of this file - DO NOT TOUCH
FORMATTING = 'UTF-8'


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

    def write(self, text):
        if len(text) != 4 and text != 'STOP':
            print('DEBUG OUT: {}'.format(text))
            self.push(bytes('{}\r\n'.format(text), FORMATTING))
        else:
            self.close()

    def handle_connect(self): 
        self.write('NICK {}'.format(self.nick))
        self.write('USER {0} {0} {0} :An IRC Bot created by linuxtinkerer'.format(self.nick))
        self.write('JOIN #test')
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
        elif type(reply) == list or type(reply) == tuple:
            for message in reply:
                self.write(message)

    def run(self, host, port): 
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(0.15)
        self.connect((host, port))
        time.sleep(0.1)
        asyncore.loop(65)


def load_builtins(shared):
    com = shared['commands']

    com['help'] = b.help_command
    com['stop'] = b.stop_command
    com['test'] = b.test_command 
    com['log'] = b.log_append_command
    com['reload'] = reload_command
    com['info'] = b.info_command
    com['commands'] = b.command_list
    com['join'] = b.join_command
    print('Loaded built-in commands')

    shared['help']['stop'] = 'Stop this bot and make it quit || :stop <password>'
    shared['help']['help'] = 'Get help about a command || :help <command> || :help :rekt'
    shared['help']['info'] = 'Get operating information about this bot || :info'
    shared['help']['test'] = 'Test to see if this bot is still working || :test'
    shared['help']['reload'] = 'Reload this bot\'s plugins || :reload'
    shared['help']['log'] = 'Write information to this bot\'s log (admins only) || :log <message> || :log this is a log message'
    shared['help']['commands'] = 'List all available commands || :commands'
    shared['help']['join'] = 'Ask for this bot to join a channel || :join <channel> || :join #bot-overlords'

    shared['cooldown']['stop'] = 5
    shared['cooldown']['help'] = 3
    shared['cooldown']['info'] = 1
    shared['cooldown']['test'] = 1
    shared['cooldown']['reload'] = 3
    shared['cooldown']['log'] = 1
    shared['cooldown']['commands'] = 10
    shared['cooldown']['join'] = 1


def load_plugins(shared: dict) -> list:
    #print(os.path.join(shared['dir'], 'plugins'))

    # Clear up existing plugins and commands
    plugin_list.clear()
    shared['commands'].clear()
    shared['help'].clear()
    shared['regexes'].clear()
    shared['re_response'].clear()

    load_builtins(shared)

    reload(plugins)
    failed_loads = []
    disabled = []

    for importer, modname, ispkg in pkgutil.iter_modules([os.path.join(shared['dir'], 'plugins')]):
        print('importing {}'.format(modname))
        try:
            module = import_module('.' + modname, package='plugins')
            reload(module)
            print('Loaded {}'.format(module))
            if module.__hasattr__('__plugin_enabled__'):
                if module.__plugin_enabled__ == True:
                    plugin_list.append(module)
                    continue

            disabled.append(module)

        except Exception as e:
            print('Couldn\'t load {}'.format(modname))
            print('Exception: {}'.format(e))
            failed_loads.append(modname)


    # TODO: Gracefully handle plugin setup fail
    for p in plugin_list:
        print('set up {}'.format(p))
        p.setup_resources(shared['conf'], shared)
        p.setup_commands(shared['commands'])

    return failed_loads, disabled


    print('{} plugins loaded!'.format(len(plugin_list)))


def reload_command(arg, packet, shared):
    '''
    Reloads all plugins as well as their data files
    '''
    print('Unloaded all plugins!')
    print('Reload command called')
    fails, disabled = load_plugins(shared)
    if len(fails) + len(disabled) == 0:
        return packet.reply('All {} plugins reloaded!'.format(len(plugin_list)))
    else:
        response = (packet.reply('{} plugins were reloaded.'.format(len(plugin_list))),
                    packet.reply('The following were NOT loaded: '))

        if len(fails) > 0:
            response += (packet.reply('Fails:  ' + ', '.join(fails)), )
        if len(disabled) > 0:
            response += (packet.reply('Disabled: '  + ', '.join(disabled)), )

        response += (packet.reply('Please check your logs for further information.'))


def load_textfile(filename):
    """Loads multiline message form a text file into a tuple"""
    with open(filename) as f:  # Pythonic
        return tuple(line.strip() for line in f)


def write_to_log(message, logname='./data/log.txt', text_format='utf-8'):
    """This function appends a line to the log file"""
    with open(logname, 'a', encoding=text_format) as logfile:
        logfile.write('[{0}] {1}\n'.format(time.strftime('%Y-%m-%d %H:%M:%S'), message))


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
        'disabled': dict(),
        }


    info_str = 'probot version {0} by linuxtinkerer'.format(VERSION)
    commands = dict()

    # This object acts as a form of persistent memory for the commands. This is particularly
    # useful for commands like `def` and `told`
    shared_data = {
        'conf': config,
        #'defs': def_dict,
        #'dict_sorted': tuple(sorted(def_dict)),
        #'is_new_words': False,
        #'told': told_tuple,
        'info': info_str,
        'chan': [],
        'dir': os.getcwd(),
        'commands': commands,
        'help': dict(),
        'regexes': dict(),
        're_response': dict(),
        'cooldown_user': dict(),
        'cooldown': dict(),
    }

    # load plugins. This *has* to happend *after* shared_data is set up
    load_plugins(shared_data)
    print('plugins: {}'.format(plugin_list))

    # TODO: Keep list of last 30 packets and the channels they are from
    return shared_data


def handle_incoming(line, shared_data):
    ''' Handles, and replies to incoming IRC messages

    line - the line to parse
    shared_data - the shared_data with literally everything in it
    '''
    print('handle_incoming: {}'.format(line))
    reply = None        # Reset reply
    msg_packet = None

    msg_packet = ircp.Packet(line)

    # Determine if prefix is at beginning of message
    # If it is, then parse for commands
    if msg_packet.msg_type == 'PRIVMSG':
        # Do we need to parse mess? If so, parse it
        msg_text = msg_packet.text
        if msg_text[0] == config['prefix'] and len(msg_text) > 1:  # If message starts with prefix
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
                reply = ircp.make_notice(('You need to wait. '
                    'Your cooldown ends in {:.1f} seconds').format(time_left), msg_packet.sender)
        else:
            for re_name in shared_data['regexes']:
                regex = shared_data['regexes'][re_name]
                if regex.match(msg_packet.text):
                    print('matched {}'.format(re_name))
                    reply = shared_data['re_response'][re_name](regex, msg_packet, shared_data)
                    break
    elif (not shared_data['conf']['logged_in']) and msg_packet.msg_type == 'NUMERIC':
        if msg_packet.numeric == ircp.Packet.numerics['RPL_ENDOFMOTD']:  # When first logging in
            reply = ircp.make_message('identify {}'.format(config['password']), 'NickServ')
            print('logging in')
            #elif msg_packet.numeric == ircp.Packet.numerics['RPL_HOSTHIDDEN']:  # If cloak applied
            print('cloak applied')
            reply = []
            for channel in config['channels'].split(' '):
                if config['intro']:
                    j, r = ircp.join_chan(channel, config['intro'])
                    reply.extend((j, r))
                else:
                    reply.append(ircp.join_chan(channel))
                print('Joining channel {}'.format(channel))
                shared_data['chan'].append(channel)
            shared_data['conf']['logged_in'] = True  # Stop checking for login numerics
        else:
            pass
    elif msg_packet.msg_type == 'PING':
        reply = 'PONG {}'.format(msg_packet.host)
    else:
        pass

    if (type(reply) == str) and (reply == 'STOP'):
        reply = [ircp.make_message('kthxbai', c) for c in shared_data['chan']]
        reply.append('STOP')  # Makes sure to close out.

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
    client.run(server, port)

    # Do any needed tying of loose ends
    # Wait for other thread to stop then close pipe
    logging.info('Shutting down m8')

    # Shutdown socket gracefully
    print('Socket closed; bye!')
