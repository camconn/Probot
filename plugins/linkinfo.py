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


__plugin_name__ = 'linkinfo'
__plugin_description__ = 'Print information about links'
__plugin_version__ = 'v0.1'
__plugin_author__ = 'Cameron Conn'
__plugin_type__ = 'regex'
__plugin_enabled__ = True

# GPLv3
# yada yada yada
# Made by lt

import requests
from bs4 import BeautifulSoup
import re  # use re instead of bs4
from urllib.parse import urlparse
from json import loads
import html.parser
import signal

import ircpacket as ircp

# From daringfireball.net, a regex of hell:
URLREGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|""" \
           r"""net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mob""" \
           r"""i|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|a""" \
           r"""m|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|b""" \
           r"""m|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|c""" \
           r"""n|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|e""" \
           r"""r|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|g""" \
           r"""n|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|i""" \
           r"""o|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|l""" \
           r"""a|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|m""" \
           r"""n|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|n""" \
           r"""o|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|q""" \
           r"""a|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|s""" \
           r"""o|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|t""" \
           r"""p|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|w""" \
           r"""s|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s(""" \
           r""")]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s""" \
           r"""()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?Â«Â»â€œâ€â€˜â€™]""" \
           r""")|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu""" \
           r"""|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|na""" \
           r"""me|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|""" \
           r"""ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|""" \
           r"""bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|""" \
           r"""cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|""" \
           r"""fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|""" \
           r"""gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|""" \
           r"""it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|""" \
           r"""lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|""" \
           r"""mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|""" \
           r"""nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|""" \
           r"""ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|""" \
           r"""su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|""" \
           r"""tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|""" \
           r"""za|zm|zw)\b/?(?!@)))"""


WEBSITES = {'www.youtube.com': '1,0You0,4Tube',
            'youtu.be': '1,0You0,4Tube',
            'kat.cr': '5,8KickassTorrents',
            'mega.co.nz': '0,4MEGA',
            'docs.python.org': '8,2PyDoc',
            'torrentfreak.com': '0,13TF',
            #'pastebin.com': '0,2PASTEBIN',
            'pastebin.com': '9>using pastebin unironically',  # le pastebin meme
            'p.hydra.ws': '1,4HP',
            'paste.hydra.ws': '1,4HP',
            'imgur.com': '9,1● 0imgur',
            'reddit.com': '4,0Leddit',
            'www.reddit.com': '4,0Leddit',
}

REQUEST_HEADERS = {
            'user-agent': 'probot - An IRC Robot (link fetcher plugin)'
}

class TimeoutException(Exception):
    """
    Called to limit size of requests
    """
    pass

def _timeout(signum, frame):
    raise TimeoutException()

def sizeof_fmt(num, suffix='B'):
    """
    Human readable size format from bytes
    From http://stackoverflow.com/a/1094933
    Credit - Fred Cirera
    """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)


def _get_page_title(link):
    """
    Get the title of an HTML page

    NOTE - all of the commented out code is old code before I learned of the
    good 'ol workaround with signals for request sizes. Therefore, it should
    stay here until this code is deemed to be stable.
    """
    #title_re = re.compile('\<title\>.*\<\/title\>', re.IGNORECASE)
    #title_tag_re = re.compile('\<\/?title\>', re.IGNORECASE)
    #printable = re.compile('[\W_]+')

    signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(3)

    title = None

    try:
        #print('fetching {}'.format(link))
        r = requests.get(link, headers=REQUEST_HEADERS, allow_redirects=True, timeout=3)
  
        if r.status_code != requests.codes.ok:
            signal.alarm(0)
            return None
        #if not 'text' in r.headers['Content-Type']:
        #    return None

        ##content_escaped = r.raw.read(4096+1, decode_content=True)
        #print('finding title')
        #h = html.parser.HTMLParser()
        soup = BeautifulSoup(r.text, 'html.parser')
  
        title = soup.title.string
  
        #escaped_content = h.unescape(str(content_escaped))
        #content = re.sub('\s+', ' ', escaped_content)
        #match = title_re.search(content)
        #print('is it a match?')
        #print(match)
        #if match != None:
        if title != None and len(title) > 0:
            #title_tagged = match.group()
            ##print(title_tagged)
            #title = title_tag_re.sub('', title_tagged)
            #title = title_tag_re.sub('', title)
            title = title.replace('\n', '')
            title = title.strip()
            ##title = printable.sub('',)


            if len(title) > 100:
                signal.alarm(0)
                return '{}...'.format(title[:99])

            #print('found one {}'.format(title))
            signal.alarm(0)
            return title.strip()
        else:
            #print('found notitle')
            pass
    except requests.exceptions.ReadTimeout as e:
        #print('Timed out m8 :(')
        print('ReadTimeout')
        signal.alarm(0)
    except requests.exceptions.Timeout as e:
        #print('Timed out m8 :(')
        print('Timeout (Requests)')
        signal.alarm(0)
    except TimeoutException as timedout:
        print('Timeout (TimeoutException)')
        signal.alarm(0)
    finally:
        signal.alarm(0)

    return title


#def _get_page_title(link):
#    """
#    Get the title of an HTML page
#    """
#    title_re = re.compile('\<title\>.*\<\/title\>', re.IGNORECASE)
#    title_tag_re = re.compile('\<\/?title\>', re.IGNORECASE)
#
#    try:
#        #print('fetching {}'.format(link))
#        r = requests.get(link, headers=REQUEST_HEADERS, allow_redirects=True, timeout=5, stream=True)
#
#        if r.status_code != requests.codes.ok:
#            return None
#        if not 'text' in r.headers['Content-Type']:
#            return None
#
#        content_escaped = r.raw.read(4096+1, decode_content=True)
#        #print('finding title')
#        h = html.parser.HTMLParser()
#        escaped_content = h.unescape(str(content_escaped))
#        content = re.sub('\s+', ' ', escaped_content)
#        match = title_re.search(content)
#        #print('is it a match?')
#        #print(match)
#        if match != None:
#            title_tagged = match.group()
#            #print(title_tagged)
#            title = title_tag_re.sub('', title_tagged)
#            title = title_tag_re.sub('', title)
#            title = title.replace('\\n', '')
#            title = title.strip()
#
#            if len(title) > 100:
#                return '{}...'.format(title[:99])
#
#            #print('found one {}'.format(title))
#            return title.strip()
#        else:
#            #print('found notitle')
#            return None
#    except requests.exceptions.ReadTimeout as e:
#        #print('Timed out m8 :(')
#        return None
#    except requests.exceptions.Timeout as e:
#        #print('Timed out m8 :(')
#        return None

def _format_page_type(page_type):
    """
    Format the file type of a page for IRC output
    """
    return '[{}]'.format(page_type)


def _get_readable_size(byte_size):
    """
    Get a human-readable format of a size of bytes
    """
    return sizeof_fmt(byte_size)


def _is_special_website(page):
    parse = urlparse(page).netloc
    return parse in WEBSITES


def _fmt_special_website(page):
    RESET = ''
    domain = urlparse(page).netloc.lower()

    title = _get_page_title(page)

    if not title:
        return None

    if domain == 'www.youtube.com' or domain == 'youtu.be':
        ending = ' - YouTube'
        if ending in title:
            chop_index = title.rfind(ending)
            return WEBSITES[domain] + RESET + ' ' + title[:chop_index]
        else:
            return title
    elif domain == 'kat.cr':
        return title.replace('KickassTorrents', WEBSITES[domain])
    elif domain == 'mega.co.nz':
        return '[text/html] ' + title.replace('MEGA', WEBSITES[domain])
    elif domain == 'docs.python.org':
        if '\u2014' in title:
            chop_index = title.find('\u2014')
            parts = title.split('\u2014')
            py_version = parts[1].strip().split()[1]
            fmt_title = '{0}{2}{3} - {1}'.format(WEBSITES[domain], parts[0][:-1], py_version, RESET)
            return fmt_title
        else:
            return title
    elif domain == 'torrentfreak.com':
        ending = '| TorrentFreak'
        if ending in title:
            return '{0}{2} - {1}'.format(WEBSITES[domain], title.split(ending)[0].strip(), RESET)
        else:
            return title
    elif domain == 'pastebin.com':
        return WEBSITES[domain]
        #ending = ' - Pastebin.com'
        #if ending in title:
        #    # Get number of lines in Paste:
        #    raw_paste = page.replace('pastebin.com/', 'pastebin.com/raw.php?i=')
        #    paste_text = requests.get(raw_paste, timeout=3).text
        #    lines = 1
        #    for char in paste_text:
        #        if char == '\n':
        #            lines += 1

        #    title = title.replace(ending, '')
        #    return '{0}{3} - {1} [{2} lines]'.format(WEBSITES[domain], title, (lines), RESET)
        #else:
        #    return title
    elif domain == 'paste.hydra.ws' or domain == 'p.hydra.ws':
        if '/api/file/' in page or '/p/' in page:
            key = page.split('/')[-1]
            r = requests.get('http://paste.hydra.ws/api/file/info/{}'.format(key))

            if r.status_code == 200:
                file_info = loads(r.text)
                title = (lambda x: file_info['title'] or '[No Title]')(0)
                ftype = file_info['filetype']
                fsize = _get_readable_size(file_info['filesize'])

                fmt_str = '{0}{4} [{1}] - {2} [Size: {3}]'

                return fmt_str.format(WEBSITES[domain], ftype, title, fsize, RESET)
                
        else:
            return title
    elif domain == 'imgur.com':
        index = title.rfind('-')
        if index >= 1:
            return '{0}{2} - {1}'.format(WEBSITES[domain], title[:index].strip(), RESET)
        else:
            return title
    elif domain == 'www.reddit.com' or domain == 'reddit.com':
        #title.replace('Reddit', '')
        return '{0}{2} - {1}'.format(WEBSITES[domain], title.strip(), RESET)
    else:
        print(domain)
        return title


def link_info(link):
    """
    Get an information string about a page such as page type and title.
    This function works with webpages and images.

    link - the webpage to find information about
    """
    if 'http://' not in link and \
       'https://' not in link:
        link = 'http://{}'.format(link)

    page_head = None
    try:
        print('requesting: {}'.format(link))
        page_head = requests.head(link, allow_redirects=True, timeout=3)
        if page_head.status_code == 404:
            page_head = requests.get(link, allow_redirects=True, timeout=3)
    except Exception as e:  # If webpage is NOT a web server
        print('Connection Refused. Sorry!')
        return None

    #print(page_head.status_code)
    #print(page_head.headers)
    #print('break 1')

    content_type = None
    try:
        content_type = page_head.headers['content-type']
    except:  # If response header is malformed
        return None
    
    # Check if webpage is a website at all
    if page_head.status_code >= 400:
        #return '[URL] Response: {}'.format(page_head.status_code)
        title = _get_page_title(link)
        if title:
            return title
        else:
            return None

    # Get rid of semicolon in content_type if it's there
    if ';' in content_type:
        content_type = content_type.split(';')[0]

    if content_type == 'text/html' and _is_special_website(link):
        return _fmt_special_website(link)
    # TODO: DO fun stuff for other types of files like PDFs, DOC files, etc.
    elif content_type == 'text/html':  # Get page title if it's an HTML page
        #print('break 3')
        fmt_type = _format_page_type(content_type)
        page_title = _get_page_title(link)
        if not page_title: 
            return None
        return '{0} {1}'.format(fmt_type, page_title)
    else:
        content_length_bytes = int(page_head.headers['Content-Length'])
        fmt_type = _format_page_type(content_type)
        content_size = _get_readable_size(content_length_bytes)
        return '{0} Size: {1}'.format(fmt_type, content_size)


def matched_url(regex, packet: ircp.Packet, shared: dict):
    ''' Match the url regex '''
    # At the moment this only cares about the first link in a message
    matched = regex.search(packet.text).group(0).strip()
    print('matched url: {}'.format(matched))
    try:
        title = link_info(matched)
        if title != None:
            return packet.reply(title)
    except Exception as e:
        print('Failed to parse link: {}'.format(matched))


def setup_resources(config: dict, shared: dict):
    url_re = re.compile(URLREGEX)
    shared['regexes']['url_re'] = url_re

    shared['re_response']['url_re'] = matched_url


def setup_commands(all_commands: dict):
    pass

