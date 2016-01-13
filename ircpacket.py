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


class Packet:
    """
    This class interprets an IRC messages' structure

    The only argument is the output received from a socket connection.

    Object properties:
    sender - name of sender or address/IP of server sending message
    sender_is_user - whether or not the sender is a user
    sender_logged_in - whether or not the sender of this message is logged in
    host - host of sender (if server, defaults to `SERVER`)
    time - time this message was sent
    target - the channel or user this PRIVMSG was directed toward
    msg_type - what type of message this is (e.g. PRIVMSG, JOIN, QUIT, PING, ACTION, numeric, etc.)
    msg_public - whether the message was sent in public chat (i.e. a channel)
    numeric - what the numeric of this message is (None if not a status message)
    text - text contents of message, if applicable
    is_action - whether the message is an action such as /me or /describe

    TODO: Look into making this class into a superclass with subclasses for
    specific types of packets (e.g. JoinPacket, MessagePacket, PingPacket, etc.)
    """

    # Dictionary of relevant numerics and their codes
    numerics = {
        'RPL_WELCOME': 1,
        'RPL_YOURHOST': 2,
        'RPL_CREATED': 3,
        'RPL_MYINFO': 4,
        'RPL_ISUPPORT': 5,
        #
        'RPL_STATSCONN': 250,
        'RPL_LUSERCLIENT': 251,
        'RPL_LUSEROP': 252,
        'RPL_LUSERUNKNOWN': 253,
        'RPL_LUSERCHANNELS': 254,
        'RPL_LUSERME': 255,
        'RPL_LOCALUSERS': 265,
        'RPL_GLOBALUSERS': 266,
        #
        'RPL_TOPIC': 332,
        'RPL_TOPICWHOTIME': 333,
        'RPL_NAMREPLY': 353,
        'RPL_ENDOFNAMES': 366,
        'RPL_INFO': 371,
        'RPL_MOTD': 372,
        'RPL_MOTDSTART': 375,
        'RPL_ENDOFMOTD': 376,
        'RPL_HOSTHIDDEN': 396}

    def __init__(self, message):
        """message - full message from socket"""
        self.sender = None
        self.sender_is_user = None
        self.sender_logged_in = None  # Unimplemented
        self.host = None
        self.time = None  # Unimplemented
        self.target = None
        self.msg_type = None
        self.msg_public = None
        self.numeric = None
        self.text = None
        self.is_action = None

        # Detect if message is valid
        #assert ':' in message != -1

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
            self.host == 'SERVER'
            if message_pt1 == 'PING' or message_pt1 == 'PONG':
                self.host = message.split(':')[1]
                self.msg_type = message_pt1

        # Make sure message is long enough to parse
        if not len(message_list) > 1:
            return

        # Attempt to parse message type from packet
        message_type = message_list[1]

        if message_type == 'PRIVMSG':
            message_target = message_list[2]
            self.sender_is_user = True
            self.msg_type = message_type

            if '#' in message_target:  # If sent to a #channel
                self.msg_public = True
                self.target = message_target
            else:
                self.msg_public = False
                self.target = message_target
        elif message_type == 'NICK':
            self.msg_type = message_type
        elif message_type == 'JOIN':
            self.msg_type = message_type
        elif message_type == 'QUIT':
            self.msg_type = message_type
        elif message_type == 'MODE':
            self.msg_type = message_type
        elif message_type == 'NOTICE':
            self.sender_is_user = False
            self.msg_public = False
            self.msg_type = message_type
        else:
            try:
                numeric_code = int(message_type)
                self.numeric = numeric_code
                self.msg_type = 'NUMERIC'
            except ValueError:
                pass

        # If IRC message is a message
        if message_type in ('PRIVMSG', 'NOTIFY', 'NUMERIC', 'NOTICE'):
            self.text = message_list[3][1:]  # The [1:] removes the :colon: from the front of the message

            # Check if message is an ACTION
            if self.text[:7] == '\001ACTION':
                self.is_action = True
                # Get rid of the '\001ACTION' at beginning of message
                # And '\001' at end of message
                self.text = self.text[8:-1]

    def reply(self, message):
        '''
        Generates a bot-like response to a user's command.

        If the command was in a public channel, then generate a message for
        the public channel. Otherwise, we shall create a NOTICE to respond
        to them with.
        '''
        if self.msg_public:
            return make_message(message, self.target)
        else:
            return make_notice(message, self.sender)


def make_message(message, target, msg_type='PRIVMSG'):
    """
    Format a message to send via PRIVMSG

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


def join_chan(channel, intro=None):
    """
    Create a join message
    """
    if intro:
        return ('JOIN {}'.format(channel), make_message(intro, channel))
    else:
        return 'JOIN {}'.format(channel)
