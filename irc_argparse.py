#!/usr/bin/env python3
'''
IRC Command parsing libary
This is a modified version of argparse to make things easier on the
developer of this program.

This module is the result of NIH syndrome

Licensed GPL v3
blah blah blah
(c) 2016 linuxtinkerer
'''

import re

def _pad_str(s, l):
    '''
    Pad string `s` to length `l`

    If len(s) >= l, this does nothing.
    '''
    if len(s) < l:
        return '{}{}'.format(s, ' '*(l-len(s)))
    return s


def parse(args) -> tuple:
    '''
    Parse a string into separate arguments, while paying attention to
    things such as quotes and escape characters. This function parses
    arguments similar to `sys.argv`.

    Returns a tuple of words.
    '''
    # Break up words
    words = []
    current_word = ''
    previous_character = None
    in_word = False
    escape_char = False
    quote_type = None

    punctuation = '!@#$%^&*()-=[]{}|<>;/?'

    def is_whitespace(char):
        if char in punctuation:
            return False
        else:
            return (re.match('[\s]', char) != None)

    quotes = ("'", '"')

    for i, c in enumerate(args):
        whitespace = is_whitespace(c)

        if in_word:
            print('i', end='')
        else:
            print('o', end='')

        if whitespace:
            print('W "', end='')
        else:
            print('N "', end='')
        
        print(c, end='": ')

        if (not whitespace) or quote_type:
            if escape_char:
                current_word += c
                escape_char = False
                print('escaped by previous char')
            elif c == '\\':
                escape_char = True
                print('backslash escapes next')
            elif c in quotes:
                if c == quote_type:
                    quote_type = None
                    print('ended quotes')
                elif quote_type == None:
                    if is_whitespace(previous_character):
                        quote_type = c
                        print('started quotes')
                    else:
                        print('quotes inside word. ignoring.')
                elif c != quote_type:
                    current_word += c
                    print('character {}'.format(c))
                else:
                    raise ParseError('Shouldn\'t have gotten here')
            else:
                # buggy fix for quotes within words
                if previous_character in quotes:
                    quote_type = previous_character
                    print('**', end='')

                current_word += c
                print('character {}'.format(c))
            in_word = True
        elif whitespace and (not quote_type):
            if in_word:
                words.append(current_word)
                in_word = False
                current_word = ''
                print('ended word')
            else:
                print('whitespace has no effect')
                pass
            in_word = False
        else:
            raise ParseError('How did we get here?')

        # last char alive
        if in_word and i == len(args)-1:
            if quote_type != None:
                #raise ParseError('Mismatched quotes!')
                print('Mismatched quotes! Ending anyways!')
                #words.append(current_word)
            if whitespace:
                words.append(current_word)
            else:
                words.append(current_word)

        previous_character = c

    print(words)
    return tuple(words)
