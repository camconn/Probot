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


import json
import requests
#import pprint
import ircpacket as ircp
from irctools import require_public

__plugin_description__ = 'Search wikipedia'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'command'
__plugin_enabled__ = True


def get_summary(query: str):
    '''
    Get the short summary for a search term

    query - The term to search for.
    '''
    BASE = 'https://en.wikipedia.org/w/'
    PAGEBASE = BASE + 'index.php'
    APIBASE = BASE + 'api.php'
    SEARCHBASE = APIBASE + '?action=opensearch&search='
    #SEARCHBASE = '{}?action=query&list=search&format=json&srsearch='
    DISAMBIGCAT = 'Category:All disambiguation pages'
    REDIRBASE = APIBASE + '?action=query&titles={}&redirects&format=json'

    headers = {'user-agent': 'probot - An IRC Bot (wiki plugin)'}
    # TODO: Use https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=tape&format=json
    # TODO: Use https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=sigkill&srprop=redirecttitle|redirectsnippet|sectionsnippet|snippet&format=json

    query = query.replace(' ', '_')
    print('new query: {}'.format(query))

    # Determine if there's a redirect
    # TODO: Handle fragments
    # NOTE: Wikipedia better handles searchs with underscores instead of spaces
    redir_req = requests.get(REDIRBASE.format(query), headers=headers)
    if redir_req.status_code == 200:
        redir_info = json.loads(redir_req.text)
        if 'redirects' in redir_info['query']:
            print('found redirect!')
            #print(redir_info['query']['redirects'])
            #print(type(redir_info['query']['redirects']))
            query = redir_info['query']['redirects'][0]['to']
            print('now using {}'.format(query))
        elif 'normalized' in redir_info['query']:
            print('normalizing query')
            query = redir_info['query']['normalized'][0]['to']
            print('now using {}'.format(query))

    # Get search info to see if anything matches
    #search_page = '{0}{1}'.format(SEARCHBASE, query)
    #print('search page: {}'.format(search_page))
    search_page = SEARCHBASE + query
    s_req = requests.get(search_page, headers=headers)

    r_list = None

    if s_req.status_code == 200:
        r_list = json.loads(s_req.text)
        #print('r_list:')
        #print(r_list)
    else:  # Some error occurred
        return 'Error: Bad status code: {}'.format(s_req.status_code)

    #pprint.pprint(r_list)

    #Check if article is disambiguation
    category_api = APIBASE + """?action=query""" \
                             """&titles={}&prop=categories""" \
                             """&format=json&continue=""".format(query)
    cat_raw = requests.get(category_api, headers=headers)
    article_cat = None
    try:
        article_cat = json.loads(cat_raw.text)
    except Exception:
        return None
    is_disambig = False

    if 'query' not in article_cat:
        return None

    #if len(r_list) < 1:
    #    return 'There were no results when searching for "{}"'.format(query)

    if 'pages' in article_cat['query']:
        pageid_cat = list(article_cat['query']['pages'].keys())[0]
        if 'categories' in article_cat['query']['pages'][str(pageid_cat)]:
            for cat in article_cat['query']['pages'][str(pageid_cat)]['categories']:
                if cat['title'] == DISAMBIGCAT:
                    is_disambig = True

    if is_disambig:
        if len(r_list[1]) >= 2:
            return 'I\'m sorry. Did you mean: {}?'.format(r_list[1][1])
        else:
            return 'Sorry, you need to be more specific.'

    # If page doesn't exists
    if len(r_list[1]) + len(r_list[2]) + len(r_list[3]) == 0:
        return 'Sorry, but I found no pages matching that title.'
    page_name = r_list[1][0]

    page_loc = None
    if len(r_list[3]) > 0:
        page_loc = r_list[3][0]
        #print(page_loc)

    # Get summary of article
    summary_api = APIBASE + """?action=query&prop=extracts""" \
                            """&explaintext&titles={}""" \
                            """&exchars=250&format=json""".format(page_name)

    summary_req = requests.get(summary_api, headers=headers)
    summary_dict = json.loads(summary_req.text)
    pageid_sum = list(summary_dict['query']['pages'].keys())[0]

    if pageid_sum:
        summary = summary_dict['query']['pages'][pageid_sum]['extract'].rstrip()
        #print('summary: ')
        #print(summary)
        #print('type: {}'.format(type(summary)))
        #print('end debug')

        # Add a link to to page location if we know it.
        if '\n' in summary or '\r' in summary:
            summary = summary.replace('\r\n', '\n').replace('\r', '\n')
            #print('split:')
            #print(summary.split('\n'))
            #print('end split')
            summary = ' '.join(summary.split('\n'))

        if page_loc:
            summary = '{} [{}]'.format(summary, page_loc)

        return summary
    else:
        return 'Sorry, but I had an error finding a summary of that page.'


@require_public
def wiki_command(arg, packet, shared):
    '''
    The wiki command

    Usage
    :w George Washington
    :wiki Monty Python
    '''
    if len(arg) < 2:
        return ircp.make_notice('You need to list something to search', packet.sender)

    query = ' '.join(arg[1:])
    print('search query: "{}"'.format(query))

    summary = get_summary(query)

    if summary == '...' or summary is None:
        return None
    elif isinstance(summary, tuple) or isinstance(summary, list):
        output = []
        for line in summary:
            output.append(ircp.make_message(line.strip(), packet.target))
        return output
    else:
        print('summary: ')
        print(summary)
        print('that was the last time!')
        return ircp.make_message(summary, packet.target)


def setup_resources(config: dict, shared: dict):
    shared['help']['wiki'] = 'Search for a term on the English Wikipedia || :wiki <query> || :wiki Linus Torvalds'
    shared['help']['w'] = 'Alias to :wiki'

    shared['cooldown']['wiki'] = 10
    shared['cooldown']['w'] = 'wiki'

def setup_commands(all_commands: dict):
    all_commands['wiki'] = wiki_command
    all_commands['w'] = wiki_command
