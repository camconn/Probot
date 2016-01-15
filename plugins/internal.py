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


__plugin_description__ = 'Internal (and non-essential) probot commands'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'command'
__plugin_enabled__ = True


from irctools import CLR_HGLT, CLR_RESET, CLR_NICK, require_auth
import ircpacket as ircp
import time


def chunk_message(msgs, num):
    """
    Chunk a iterator into num-unit chunks and return them for easy transmittal
    via direct chat.

    Arguments:
        msgs - the iterator to be chunked
        num - the number of items the iterator is to be chunked into
    """
    for sublist in range(0, len(msgs), num):
        yield msgs[sublist:sublist + num]


def write_to_log(message, logname='./data/log.txt', text_format='utf-8'):
    """This function appends a line to the log file"""
    with open(logname, 'a', encoding=text_format) as logfile:
        logfile.write('[{0}] {1}\n'.format(time.strftime('%Y-%m-%d %H:%M:%S'), message))


def info_command(arg, packet, shared):
    """
    Displays information about this bot
    """
    print('Info command called')
    return ircp.make_notice(shared['info'], packet.sender)


def help_command(arg, packet, shared):
    print('Help command called')

    if len(arg) < 2:
        return ircp.make_notice('Usage - `:help <command>` || Example - :help :told', packet.sender)

    c = arg[1].lower().replace(':', '')

    if c in shared['help']:
        return ircp.make_notice(':{} - {}'.format(c, shared['help'][c]), packet.sender)
    else:
        return ircp.make_notice('Help is not available (yet) for `{}`'.format(arg[1]), packet.sender)


@require_auth
def say_command(arg: tuple, packet: ircp.Packet, shared: dict):
    """
    Echoes text than an admin tells the bot to
    """
    if len(arg) < 2:
        return packet.reply('You must specify a channel for me to say that in')
    else:
        target = arg[1]
        message = packet.text.split(target)[1].lstrip()
        return (packet.reply('Message sent to {}'.format(target)),
                ircp.make_message(message, target))


def command_list(arg, packet, shared):
    '''
    Lists all commands
    '''
    print('listing commands!')
    all_commands = shared['commands']
    response = [ircp.make_notice('Available commands ({} total)'.format(len(all_commands)), packet.sender),]
    response.extend(ircp.make_notice(c, packet.sender) for c in sorted(all_commands))
    return response


#def spam_command(arg, packet, shared):
#    if packet.sender in shared['conf']['admin']:
#
#        args = arg.split(' ', 2)
#        try:
#            spam_target = args[0].strip()
#            spam_num = int(args[1])
#            spam_str = args[2]
#
#            muh_spam = tuple(ircp.make_message(spam_str, spam_target) for item in range(spam_num))
#            return muh_spam
#        except:
#            return ircp.make_notice('An error occurred', packet.sender)
#    else:
#        return ircp.make_notice('You must be admin for this command', packet.sender)

def test_command(arg, packet, shared):
    """
    Respond to command by telling user that the bot is listening
    and working as intended

    This command takes no arguments
    """
    print('test command called')
    fmt_str = '{0}{1}{2} reporting in! Type {3}:help{2}.'
    test_str = fmt_str.format(CLR_NICK, shared['conf']['bot_nick'], CLR_RESET, CLR_HGLT)
    if packet.msg_public:
        return ircp.make_message(test_str, packet.target)
    else:
        return ircp.make_notice(test_str, packet.sender)


@require_auth
def log_append_command(arg, packet, shared):
    """ Appends something to text logs

    arg - the text to append to the log

    User syntax is `arg <text>` where `<text>` is a message that will be added
    to the log.
    """
    if len(arg) < 2:
        return packet.reply('You need to put something down for me to add!')

    text = packet.text.split(':log')[1].lstrip()
    write_to_log('{0} LOG-APPEND: {1}'.format(packet.sender, arg))
    return ircp.make_message('Log written', packet.sender)


@require_auth
def join_command(arg: tuple, packet: ircp.Packet, shared: dict):
    ''' Make the bot join a channel

        :join <channel> [channel [channel ...]]
    '''
    output = None
    if len(arg) < 2:
        output = packet.reply('You need to specify a channel for me to join.')
    else:
        output = []
        for c in arg[1:]:
            if c.find('#') == 0:
                output.append(ircp.join_chan(c))
            else:
                output.append(packet.reply('{} is not a valid channel'.format(c)))

        output.append(packet.reply('Joined!'))

    return output


@require_auth
def part_command(arg: tuple, packet: ircp.Packet, shared: dict):
    ''' Make the bot part a channel

        :part <channel> [channel [channel ...]]
    '''
    output = None
    if packet.sender in shared['auth']:
        if len(arg) < 2:
            output = packet.reply('You need to specify a channel for me to join.')
        else:
            output = []
            for c in arg[1:]:
                if c in shared['chan']:
                    output.append(ircp.leave_chan(c))
                    shared['chan'].remove(c)
                else:
                    output.append(packet.reply('I am currently not in {}'.format(c)))

            output.append(ircp.make_notice('Done PARTing', packet.sender))
    else:
        output = packet.reply('You do not have permission to do that. You need to :auth')

    print(output)
    return output


@require_auth
def list_channels(arg: tuple, packet: ircp.Packet, shared: dict):
    ''' List channels that this bot is currently in '''
    output = None
    if packet.sender in shared['auth']:
        output = []
        output.append(packet.reply('I am currently in: '))

        for c in shared['chan']:
            output.append(packet.reply(c))
    else:
        output = packet.reply('You do not have permission to do that. You need to :auth')

    return output


def setup_resources(config: dict, shared: dict):
    shared['help']['help'] = 'Get help about a command || :help <command> || :help :rekt'
    shared['help']['info'] = 'Get operating information about this bot || :info'
    shared['help']['test'] = 'Test to see if this bot is still working || :test'
    shared['help']['log'] = 'Write information to this bot\'s log (admins only) || :log <message> || :log this is a log message'
    shared['help']['commands'] = 'List all available commands || :commands'
    shared['help']['join'] = 'Ask for this bot to join a channel || :join <channel> || :join #bot-overlords'
    shared['help']['part'] = 'Ask for this bot to part a channel || :part <channel> || :part #lol'
    shared['help']['say'] = 'Make the bot say something (admins only) || :say <target> <message> || :say seth you suck || :say #default hello, world!'
    shared['help']['channels'] = 'List the channels this bot is currently in || :channels'

    shared['cooldown']['help'] = 3
    shared['cooldown']['info'] = 1
    shared['cooldown']['test'] = 1
    shared['cooldown']['log'] = 1
    shared['cooldown']['commands'] = 10
    shared['cooldown']['join'] = 2
    shared['cooldown']['part'] = 'join'
    shared['cooldown']['say'] = 3
    shared['cooldown']['channels'] = 5


def setup_commands(all_commands: dict):
    com = all_commands

    com['help'] = help_command
    com['test'] = test_command 
    com['log'] = log_append_command
    com['info'] = info_command
    com['commands'] = command_list
    com['join'] = join_command
    com['say'] = say_command
    com['part'] = part_command 
    com['channels'] = list_channels

