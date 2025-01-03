**NAME**


``MEH`` - mekker


**SYNOPSIS**


|
| ``meh <cmd> [key=val] [key==val]``
| ``meh -cviw
| ``meh -d`` 
| ``meh -s``
|

**DESCRIPTION**


``MEH`` has all you need to program a unix cli program, such as disk
perisistence for configuration files, event handler to handle the
client/server connection, deferred exception handling to not crash
on an error, etc.

``MEH`` contains all the python3 code to program objects in a functional
way. It provides a base Object class that has only dunder methods, all
methods are factored out into functions with the objects as the first
argument. It is called Object Programming (OP), OOP without the
oriented.

``MEH`` allows for easy json save//load to/from disk of objects. It
provides an "clean namespace" Object class that only has dunder
methods, so the namespace is not cluttered with method names. This
makes storing and reading to/from json possible.

``MEH`` is a demo bot, it can connect to IRC, fetch and display RSS
feeds, take todo notes, keep a shopping list and log text. You can
also copy/paste the service file and run it under systemd for 24/7
presence in a IRC channel.

``MEH`` is Public Domain.


**INSTALL**


installation is done with pipx

|
| ``$ pipx install meh``
| ``$ pipx ensurepath``
|
| <new terminal>
|
| ``$ meh srv > meh.service``
| ``$ sudo mv meh.service /etc/systemd/system/``
| ``$ sudo systemctl enable meh --now``
|
| joins ``#meh`` on localhost
|


**USAGE**


use ``meh`` to control the program, default it does nothing

|
| ``$ meh``
| ``$``
|

see list of commands

|
| ``$ meh cmd``
| ``cfg,cmd,dne,dpl,err,exp,imp,log,mod,mre,nme,``
| ``now,pwd,rem,req,res,rss,srv,syn,tdo,thr,upt``
|

start daemon

|
| ``$ mehd``
| ``$``
|

start service

|
| ``$ mehs``
| ``<runs until ctrl-c>``
|


**COMMANDS**


here is a list of available commands

|
| ``cfg`` - irc configuration
| ``cmd`` - commands
| ``dpl`` - sets display items
| ``err`` - show errors
| ``exp`` - export opml (stdout)
| ``imp`` - import opml
| ``log`` - log text
| ``mre`` - display cached output
| ``now`` - show genocide stats
| ``pwd`` - sasl nickserv name/pass
| ``rem`` - removes a rss feed
| ``res`` - restore deleted feeds
| ``req`` - reconsider
| ``rss`` - add a feed
| ``syn`` - sync rss feeds
| ``tdo`` - add todo item
| ``thr`` - show running threads
| ``upt`` - show uptime
|

**CONFIGURATION**


irc

|
| ``$ meh cfg server=<server>``
| ``$ meh cfg channel=<channel>``
| ``$ meh cfg nick=<nick>``
|

sasl

|
| ``$ meh pwd <nsvnick> <nspass>``
| ``$ meh cfg password=<frompwd>``
|

rss

|
| ``$ meh rss <url>``
| ``$ meh dpl <url> <item1,item2>``
| ``$ meh rem <url>``
| ``$ meh nme <url> <name>``
|

opml

|
| ``$ meh exp``
| ``$ meh imp <filename>``
|


**PROGRAMMING**


``meh`` runs it's modules in the package, so you have to clone from git

|
| ``$ git clone ssh://git@github.com/otpcr/meh``
|

edit a file in meh/modules/<name>.py and add the following for ``hello world``

::

    def hello(event):
        event.reply("hello world !!")


save this and edit ``meh/modules/face.py`` and import your filename in there.
install that with ``pipx install . --force``, your program can execute the
``hello`` command now.


|
| ``$ meh hello``
| ``hello world !!``
|

commands run in their own thread, errors are deferred to not have loops
blocking/breaking on exception and can contain your own written python3
code, see the meh/modules directory for examples.


**SOURCE**


source is at `https://github.com/otpcr/meh  <https://github.com/otpcr/meh>`_


**FILES**

|
| ``~/.meh``
| ``~/.local/bin/meh``
| ``~/.local/pipx/venvs/meh/*``
|

**AUTHOR**

|
| ``Bart Thate`` <``bthate@dds.nl``>
|

**COPYRIGHT**

|
| ``MEH`` is Public Domain.
|