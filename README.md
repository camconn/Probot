Probot
======

Probot is a **P**ython3 IRC **robot** with the ability to have plugins.

About
-----
This is an IRC bot written in Python 3.
The aim of Probot is to be responsive, fast, and easily extended.  Probot strives
to be an example of what quality Python code looks like.  Moreover, it should give 
new programmers to the Python language an idea of what you can do with a little
bit of knowledge and of free time.

Probot is written for maximum lulz and utility.  It probably has more features
than it should have. Oh well! The feature creep will only expand in the future!

Features
--------
A quick list of features of Probot. Probot has many features, most of them useless,
or meant for crude, stupid jokes.

### Completed
- Asynchronous for snappy performance
- Multiple channel support
- Easily to install plugins to add commands and functionality.
    - No need to restart the bot, just run `:reload`!
- Login to a reserved nickname (ie NickServ)
    - Wait for cloak or vHost before connecting to channel
- Custom command prefixes (eg `.` or `!` or `>`)
- Command aliases - `:convert` can become `:c`
- Command throttling (via cooldowns per command)
- Built-in commands:
    - `:auth` - authenticate yourself as a bot operator
    - `:help` - get psychiatric counseling
    - `:commands` - list available commands
    - `:test` - check to see if the bot is working
    - `:info` - display version and bot information
    - `:reload` - reload external plugins **on the fly!**
    - `:join` - join a channel (admins only)
    - `:stop` - stop this irc bot (admins only)
    - `:log` - write something to log (admins only)
    - `:plugins` - list available plugins
    - `:plugin` - get information about a plugin
- Default plugin commands:
    - `:calc` - simple calculator
    - `:convert` - currency conversion
    - `:currencies` - list available currencies to convert between
    - `:[not]told` - get #told
    - `:[not]rekt` - get #rekt
    - `:partyboat` - start the party boat
    - `:whatis` - look up the long name for a currency identifier
    - `:wiki` - search wikipedia for a term
- Plugins to recognize text
    - Link identifier
        - Customized feedback about YouTube, Imgur, Reddit, Hydra Paste, and
          more!
        - Display file sizes and types (e.g. PDF, ISO, ZIP, GZIP)
        - Many more sites
    - Responses to complements, greetings, and mean words from users
- Substitution plugin
    - Fix typos just by running `s/tpyo/typo/` like you would in Vim

### In-Progress
- Enabling and disabling plugins via commands or configuration

### Planned
- Google search plugin (`:google`)

Setup
-----

### Installing and Running
The setup is very simple. Install some modules and you're good!
1) Copy this code to somewhere on your computer.
2) Install required pip modules: `pip install requests bs4 hurry.filesize` should do it. Use a virtualenv if you want.
3) Copy `config.template.json` to `config.json`.
4) Edit `config.json` to your liking. The options are self-explanatory.
5) If you aren't using the OpenExchangeRates API, then disable the plugin or all hell will break loose.
6) Run `./probot` to start the bot.
7) ???
8) PROFIT!!!

### Creating a Plugin
To create a plugin, create a copy of `plugins/template.py`, and read the included
instructions on how to create a plugin.

License
-------
All of this code is licensed under the GNU Affero License Version 3 or any later
version. The full text of this license can be found in the LICENSE file.
