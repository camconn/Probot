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


import ircpacket as ircp


CLR_HGLT = '3'
CLR_RESET = ''
CLR_NICK = '11'


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


#def echo_command(arg, packet, shared):
#    """
#    Echoes text than an admin tells the bot to
#    """
#    channel, words = arg.split(' ', 1)
#
#    if packet.sender.lower() != shared['conf']['admin']:
#        h8_string = 'u wot m8? pls stop trying to abuse this bot.'
#        return ircp.make_message(h8_string, packet.sender)
#    elif channel.lower() not in shared['chan']:
#        return ircp.make_notice('Sorry, I\'m not in that channel at the moment', packet.sender)
#    else:
#        return ircp.make_message(words, channel)


def stop_command(arg: list, packet: ircp.Packet, shared: dict):
    '''
    Stops this bot
    '''
    import logging
    print('Stop command called')
    sender = packet.sender.lower()
    if len(arg) == 2 and arg[1] == shared['conf']['adminpass']:
        logging.info('STOP command received; stopping bot.')
        return 'STOP'
    else:
        write_to_log('User {0} tried to run `stop` command.'.format(packet.sender))
        return_msg = ('STOP TRYING TO BREAK THIS BOT, ASSHOLE. THIS INCIDENT '
                      'WILL BE REPORTED TO SANTA CLAUS, ANONYMOOSE, THE '
                      'HACKER 4CHAN, TEH FBI, THE CIA, AND THE NSA!!!111!!one!1')
        return ircp.make_notice(return_msg, packet.sender)


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


def log_append_command(arg, packet, shared):
    """ Appends something to text logs

    arg - the text to append to the log

    User syntax is `arg <text>` where `<text>` is a message that will be added
    to the log.
    """
    if packet.sender == shared['conf']['admin']:
        write_to_log('{0} LOG-APPEND: {1}'.format(packet.sender, arg))
        return ircp.make_message('Log written', packet.sender)
    else:
        write_to_log('{0} failed to write to log: {1}'.format(packet.sender, arg))
        alert_string = ('You do not have sufficient permissions to do this. '
                        'This incident shall be reported')
        return ircp.make_message(alert_string, packet.sender)


def join_command(arg, packet, shared):
    ''' Make the bot to join a channel

        :join <channel>
    '''
    if len(arg) < 2:
        return packet.reply('You must specify a channel for me to join!')

    if packet.sender.lower() == shared['conf']['admin'].lower():
        chan = arg[1]
        if chan.find('#') == 0:
            shared['chan'].append(chan)
            raw_commands = ircp.join_chan(chan, shared['conf']['intro'])

            if type(raw_commands) == tuple:
                return raw_commands + (packet.reply('Channel "{}" joined'.format(chan)),)
            else:
                return (raw_commands, packet.reply('Channel "{}" joined.'.format(chan)))
        else:
            return ircp.make_notice('# not fond in channel name', packet.sender)
    else:
        #return ircp.make_message('You do not have permission for this command', packet.sender)
        return packet.reply('You do not have permission to perform this command.')

