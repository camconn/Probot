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
IRCPacket - A simplification of IRC Events

This file includes a Packet object, as well as a few functions
to make handling IRC a little easier.
'''


from collections import namedtuple
import re

_Numerics = namedtuple('Numerics',
                       ('RPL_WELCOME',
                        'RPL_YOURHOST',
                        'RPL_CREATED',
                        'RPL_MYINFO',
                        'RPL_ISUPPORT',
                        'RPL_STATSCONN',
                        'RPL_LUSERCLIENT',
                        'RPL_LUSEROP',
                        'RPL_LUSERUNKNOWN',
                        'RPL_LUSERCHANNELS',
                        'RPL_LUSERME',
                        'RPL_LOCALUSERS',
                        'RPL_GLOBALUSERS',
                        'RPL_TOPIC',
                        'RPL_TOPICWHOTIME',
                        'RPL_NAMREPLY',
                        'RPL_ENDOFNAMES',
                        'RPL_INFO',
                        'RPL_MOTD',
                        'RPL_MOTDSTART',
                        'RPL_ENDOFMOTD',
                        'RPL_HOSTHIDDEN'))

numerics = _Numerics(
    RPL_WELCOME=1,
    RPL_YOURHOST=2,
    RPL_CREATED=3,
    RPL_MYINFO=4,
    RPL_ISUPPORT=5,
    RPL_STATSCONN=250,
    RPL_LUSERCLIENT=251,
    RPL_LUSEROP=252,
    RPL_LUSERUNKNOWN=253,
    RPL_LUSERCHANNELS=254,
    RPL_LUSERME=255,
    RPL_LOCALUSERS=265,
    RPL_GLOBALUSERS=266,
    RPL_TOPIC=332,
    RPL_TOPICWHOTIME=333,
    RPL_NAMREPLY=353,
    RPL_ENDOFNAMES=366,
    RPL_INFO=371,
    RPL_MOTD=372,
    RPL_MOTDSTART=375,
    RPL_ENDOFMOTD=376,
    RPL_HOSTHIDDEN=396
)


class Packet:  # pylint: disable=too-many-instance-attributes
    """
    This class interprets an IRC messages' structure

    The only argument is the output received from a socket connection.

    Object properties:
    sender - name of sender or address/IP of server sending message
    sender_is_user - whether or not the sender is a user
    host - host of sender (if server, defaults to `SERVER`)
    target - the channel or user this PRIVMSG was directed toward
    msg_type - what type of message this is (e.g. PRIVMSG, JOIN, QUIT, PING, ACTION, numeric, etc.)
    msg_public - whether the message was sent in public chat (i.e. a channel)
    text - text contents of message, if applicable
    is_action - whether the message is an action such as /me or /describe
    nick_from - with NICK commands, tells what nick the user changed from
    nick_to - with NICK commands, tells what nick the user changed to
    """
    __slots__ = ('sender', 'host', 'target', 'msg_type',
                 'numeric', 'text', 'is_action', 'nick_to')

    def __init__(self, message):
        """message - full message from socket"""
        self.sender = None
        self.host = None
        self.target = None
        self.msg_type = None
        self.numeric = None
        self.text = None
        self.is_action = None
        self.nick_to = None

        message_list = message.split(' ', 3)  # split message at each space

        # Check if message is sent by a user
        message_pt1 = message_list[0]

        try:
            user_end = message_pt1.index('!')
            host_begin = message_pt1.index('@') + 1
            if ('!' in message_pt1) and ('@' in message_pt1):
                self.sender = message_pt1[1:user_end]
                self.host = message_pt1[host_begin:]
        except ValueError:
            self.host = 'SERVER'
            if message_pt1 == 'PING' or message_pt1 == 'PONG':
                print('got a PING')
                self.host = message.split(':')[1].strip()
                self.msg_type = message_pt1
                print('host: {}'.format(self.host))
                return

        # Make sure message is long enough to parse
        if not len(message_list) > 1:
            return

        # Attempt to parse message type from packet
        message_type = message_list[1]

        numeric_match = re.match('[0-9]{1,3}', message_type)

        if numeric_match:
            try:
                numeric_code = int(message_type)
                self.numeric = numeric_code
                self.msg_type = 'NUMERIC'
            except ValueError:
                pass
        else:
            if message_type == 'PRIVMSG':
                message_target = message_list[2]
                self.msg_type = message_type
                self.target = message_target
            elif message_type == 'JOIN':
                self.msg_type = message_type
                self.target = message_list[2][1:]
            else:
                self.msg_type = message_type

        # If IRC message is a message
        if message_type in ('PRIVMSG', 'NOTIFY', 'NUMERIC', 'NOTICE'):
            # The [1:] removes the :colon: from the front of the message
            self.text = message_list[3][1:]

            # Check if message is an ACTION
            if self.text[:7] == '\001ACTION':
                self.is_action = True
                # Get rid of the '\001ACTION' at beginning of message
                # And '\001' at end of message
                self.text = self.text[8:-1]
        elif message_type == 'NICK':
            self.nick_to = message_list[2][1:]

    @property
    def sender_is_user(self):
        ''' Determine if this event was caused by a user '''
        return self.host == 'SERVER' or '@' not in self.host

    @property
    def msg_public(self):
        ''' Is this event public to all users? '''
        return '#' in self.target

    def reply(self, message):
        '''
        Generates a response to a user's command depending on whether the
        message sent in a public or private context.

        If this (object's) message was sent in a public channel, then
        generate a message for the public channel. Otherwise, a NOTICE
        response will generated.

        message - the message to send
        '''
        if self.msg_public:
            return make_message(message, self.target)
        else:
            return self.notice(message)

    def notice(self, message):
        ''' Generates a NOTICE response to a user. This is useful to
        prevent from spamming chat needlessly.

        message - the message to send
        '''
        return make_notice(message, self.sender)


def make_message(message, target, msg_type='PRIVMSG'):
    """
    Format a message to send via PRIVMSG.

    message - the message to send
    target - the user or channel to send the message to
    msg_type - the type of message to send (default PRIVMSG, also accepted: NOTIFY)

    Returns a formatted string to send through socket connection to IRC
    """
    return '{0} {1} :{2}'.format(msg_type, target, message)


def make_notice(message, target):
    """
    Format a message to send via NOTICE

    message - the message to send
    target - the user or channel to send the message to
    msg_type - the type of message to send (default PRIVMSG, also accepted: NOTIFY)

    Returns a formatted string to send through socket connection to IRC
    """
    return make_message(message, target, msg_type='NOTICE')


def join_chan(channel: str):
    ''' Generate a join message '''
    return 'JOIN {}'.format(channel)


def leave_chan(channel: str):
    ''' Generate a leave message '''
    return 'PART {}'.format(channel)
