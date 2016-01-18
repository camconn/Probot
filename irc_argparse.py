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
Command parsing libary

This file is used to help parse argument for probot.
All of the interesting stuff is located in the parse
function.
'''

import re
import logging


SYMBOLS = set('!@#$%^&*()_-=[]{}|<>;/?')
QUOTES = set(""""\'""")


def _pad_str(string, length):
    '''
    Pad string `s` to length `l`

    If len(s) >= l, this does nothing.
    '''
    if len(string) < length:
        return '{}{}'.format(string, ' ' * (length - len(string)))
    return string


def _is_whitespace(char):
    ''' Figure out if this character is whitespace or not '''
    if char in SYMBOLS:
        return False
    else:
        return re.match(r'[\w]', char) is None


def parse(args) -> tuple:  # pylint: disable=too-many-branches,too-many-statements
    ''' Parse a string into separate arguments, while paying
    attention to things such as quotes and escape characters.
    This function parses arguments similar to `sys.argv`.

    Probot uses this instead of shutil because shutil likes to
    blow up when there are mismatched quotes. This function
    simply ignores mismatched quotes.

    This method disables the pylint `too-many-branches` warning
    because this problem, by nature, is complex.

    Returns a tuple of words.
    '''
    logging.debug(args)
    # Break up words
    words = []
    current_word = ''
    previous_character = None
    in_word = False
    escape_char = False
    quote_type = None

    for i, ch in enumerate(args):
        whitespace = _is_whitespace(ch)

        # debug_out = ''
        # if in_word:
        #     debug_out = 'i'
        # else:
        #     debug_out = 'o'

        # if whitespace:
        #     debug_out = '{}W'.format(debug_out)
        #     # logging.debug('W "', end='')
        # else:
        #     debug_out = '{}N'.format(debug_out)
        #     # logging.debug('N "', end='')

        # debug_out = '{} "{}": '.format(debug_out, ch)
        # logging.debug(debug_out)

        if (not whitespace) or quote_type:
            if escape_char:
                current_word += ch
                escape_char = False
                logging.debug('escaped by previous char')
            elif ch == '\\':
                escape_char = True
                logging.debug('backslash escapes next')
            elif ch in QUOTES:
                if ch == quote_type:
                    quote_type = None
                    logging.debug('ended quotes')
                elif quote_type is None:
                    if _is_whitespace(previous_character):
                        quote_type = ch
                        logging.debug('started quotes')
                    else:
                        logging.debug('quotes inside word. ignoring.')
                elif ch != quote_type:
                    current_word += ch
                    logging.debug('character %s', ch)
                else:
                    raise Exception('Shouldn\'t have gotten here')
            else:
                # buggy fix for quotes within words
                if previous_character in QUOTES:
                    quote_type = previous_character
                    # logging.debug('**', end='')

                current_word += ch
                logging.debug('character %s', ch)
            in_word = True
        elif whitespace and (not quote_type):
            if in_word:
                words.append(current_word)
                in_word = False
                current_word = ''
                logging.debug('ended word')
            else:
                logging.debug('whitespace has no effect')
            in_word = False
        else:
            raise Exception('How did we get here?')

        # last char alive
        if in_word and i == len(args) - 1:
            # if quote_type is None:
            #     logging.debug('Mismatched quotes! Ending anyways!')
            if whitespace:
                words.append(current_word)
            else:
                words.append(current_word)

        previous_character = ch

    print(words)
    return tuple(words)
