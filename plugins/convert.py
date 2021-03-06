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

import requests
import json
from time import time
import ircpacket as ircp

__plugin_description__ = 'Convert between currencies'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'command'
__plugin_enabled__ = True

CURRENCIES = dict()
ALIASES = {'US': 'USD',
           'EU': 'EUR',
           'BITCOIN': 'BTC',
           'BITCOINS': 'BTC',
           'DOLLAR': 'USD',
           'DOLLARS': 'USD',
           'POUND': 'GBP',
           'POUNDS': 'GBP',
           'EURO': 'EUR',
           'EUROS': 'EUR',
           'RUBLE': 'RUB',
           'RUBLES': 'RUB',
           'YEN': 'JPY',
           'CANADA': 'CDN',
           'CANADIAN': 'CDN',
           'AUS': 'AUD',
           'MONOPOLY': 'USD',
           'MONEY': 'USD',
           'MONOPOLY MONEY': 'USD',
           'UDS': 'USD',
           'CRAP': 'USD'}

API_URL = 'https://openexchangerates.org/api/latest.json?app_id={}'


def get_rates(shared: dict):
    ''' Get conversion rates either from cache or via the
    OpenExchangeRates API'''
    if ('convert.time' in shared) and ('convert.cache' in shared) and \
            (shared['convert.time'] + 3600 * 12 > time()):
        #print(shared['convert.cache'])
        print('loading from cache!')
        return shared['convert.cache']
    else:
        r = requests.get(API_URL.format(shared['conf']['oxr_id']))

        if r.status_code != requests.codes.ok:
            return 'There was an error fulfilling the request. Try again later.'

        shared['convert.cache'] = str(r.text)
        shared['convert.time'] = time()
        print('no cache!')
        #print(shared['convert.cache'])
        return r.text


def currency_rate(rates: dict, currency: str) -> float:
    if currency in rates:
        return float(rates[currency])
    return 0.0


def get_conversion(arg: tuple, shared: dict):
    print('args: {}'.format(arg))

    data = get_rates(shared)
    if 'error' in data:
        return

    conversions = json.loads(data)
    conversions['rates']['USD'] = str(1.000)

    initial_amount, type_from, type_to = 0.0, '', ''
    try:
        initial_amount = float(arg[0])
        type_from = str(arg[1]).upper()
        type_to = str(arg[len(arg) - 1]).upper()
    except ValueError:
        return 'You need to specify a valid number to convert *from*'

    if type_from in ALIASES:
        type_from = ALIASES[type_from]
    if type_to in ALIASES:
        type_to = ALIASES[type_to]

    if type_from not in CURRENCIES:
        return ('"{}" is not a valid currency. '
                'Type :currencies to see available types.'.format(type_from))
    if type_to not in CURRENCIES:
        return ('"{}" is not a valid currency. '
                'Type :currencies to see available types.'.format(type_to))

    rate_from = currency_rate(conversions['rates'], type_from)
    rate_to = currency_rate(conversions['rates'], type_to)

    print('rate from: {}\nrate to: {}'.format(rate_from, rate_to))

    if rate_from == 0 or rate_to == 0:
        print('an error occurred')
        return None

    final_amount = initial_amount / rate_from * rate_to

    return '{} {} is {:.3f} {}'.format(initial_amount, type_from, final_amount, type_to)


def convert_command(arg: tuple, packet: ircp.Packet, shared: dict):

    if len(arg) < 5:
        return (packet.notice('You need to specify an amount, original current, and output currency!'),
                packet.notice('For example - :convert $50 USD to Pounds'))

    conversion = get_conversion(arg[1:], shared)

    if conversion == '' or conversion is None:
        return None
    else:
        return packet.reply('{}: {}'.format(packet.sender, conversion))


def list_currencies(arg: tuple, packet: ircp.Packet, shared: dict):
    c_list = [packet.notice('Available currencies: ({} total)'.format(len(CURRENCIES)))]
    c_list.extend(packet.notice(c) for c in sorted(CURRENCIES))
    return c_list


def whatis_command(arg: tuple, packet: ircp.Packet, shared: dict):
    if len(arg) < 2:
        return ircp.make_notice('You must specify a type of currency!', packet.sender)

    orig_currency = (' '.join(arg[1:]))
    currency = str(orig_currency).upper()

    if currency in ALIASES:
        currency = ALIASES[currency]

    if currency not in CURRENCIES:
        return ircp.make_notice('I don\'t know what "{}" is!'.format(currency), packet.sender)
    else:
        return packet.reply('{} is {}'.format(orig_currency, CURRENCIES[currency]))


def setup_resources(config: dict, shared: dict):
    from os import path

    currency_file = path.join(shared['dir'], 'data/currencies.json')
    currency_string = ''
    with open(currency_file, 'rt') as f:
        for line in f:
            currency_string += line

    curr_dict = json.loads(currency_string)
    for k in curr_dict:
        CURRENCIES[k] = curr_dict[k]

    shared['help']['convert'] = 'Convert one currency to another || :convert 50 USD to GBP'
    shared['help']['c'] = 'Alias to :convert'
    shared['help']['currency'] = 'Alias to :currencies || :currency'
    shared['help']['currencies'] = 'View available currencies to convert between || :currencies'
    shared['help']['whatis'] = 'View the long version of a currency abbreviation || :whatis <currency> || :whatis BTC'

    shared['cooldown']['convert'] = 2
    shared['cooldown']['c'] = 'convert'
    shared['cooldown']['currency'] = 20
    shared['cooldown']['currencies'] = 'currency'
    shared['cooldown']['whatis'] = 2


def setup_commands(all_commands: dict):
    all_commands['convert'] = convert_command
    all_commands['c'] = convert_command
    all_commands['currencies'] = list_currencies
    all_commands['currency'] = list_currencies
    all_commands['whatis'] = whatis_command
