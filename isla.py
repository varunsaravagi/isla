#!/usr/bin/env python
# -*- coding: utf-8 -*-
import irc.bot
import importlib
import inspect
import glob
import re
import sys
import traceback

import bot
import config

__version__ = '0.0.2'

class Isla(irc.bot.SingleServerIRCBot):
    def __init__(self, *args, **kwargs):
        super(Isla, self).__init__(*args, **kwargs)

        self.binds = {}
        self.binds["reply"] = {}
        self.binds["hear"] = {}

    def on_nicknameinuse(self, c, e):
        old = c.get_nickname()
        new = old + "_"
        print "Warning: Nick '{old}' in use, trying '{new}'".format(old=old,new=new)
        c.nick(new)

    def on_welcome(self, c, e):
        # Identify
        print "Notice: Hello world! Connected and identifying."
        c.privmsg('NickServ', 'IDENTIFY {password}'.format(password=config.nickserver_password))
        # Join autojoin channels
        for channel in self.autojoin:
            print "Notice: Autojoining channel {channel}".format(channel=channel)
            c.join(channel)

    def on_pubmsg(self, c, e):
        at_me = False
        msg = e.arguments[0].strip()

        if msg.startswith(c.get_nickname() + ":") or msg.startswith(c.get_nickname() + ","):
            at_me = True
            msg = msg[len(c.get_nickname()) + 1:].strip()

        if at_me:
            self.match_bind('reply', c, e, msg)
        else:
            self.match_bind('hear', c, e, msg)

    def match_bind(self, bind_type, c, e, msg):
        for k, v in self.binds[bind_type].iteritems():
            plugin, source = k
            match, func = v
            result = match.match(msg)
            if result:
                try:
                    func(self, c,e,msg,result)
                except:
                    print "Exception in plugin {mod}.{func} /{bind}/".format(mod=plugin,func=func.__name__,bind=source)
                    traceback.print_exc(file=sys.stdout)

    def get_version(self):
        return "isla [bot] {version}".format(version=__version__)

    def reply(self, c, e, msg):
        c.privmsg(e.target, "{nick}: {msg}".format(nick=e.source.nick,msg=msg))

    def send(self, c, e, msg):
        c.privmsg(e.target, msg)

    def bind(self, bind_type, plugin, match, func, i=False):
        if not bind_type in self.binds:
            raise ValueError("Invalid bind type: {type}".format(bind_type))
        flags = re.U | (re.I if i else 0)
        x = re.compile(match, flags)
        if x:
            self.binds[bind_type][(plugin,match)] = (x, func)
        else:
            raise ValueError("Bad regex: {match}".format(match))

if __name__ == "__main__":
    bot.isla = Isla([config.server], "isla", "isla")
    bot.isla.autojoin = config.autojoin
    bot.isla.mods = {}
    # Bind plugins
    r = re.compile("^mods\/(.*)\.py$")
    for mod in glob.glob("mods/*.py"):
        name = r.match(mod).group(1)
        if name == "__init__": continue
        print "Loading module {mod}...".format(mod=name)
        bot.isla.mods[name] = importlib.import_module("mods.{name}".format(name=name))
    bot.isla.start()

def bind(bind_type, match, i=False):
    def real_bind(func):
        bot.isla.bind(bind_type, inspect.getmodule(func).__name__, match, func, i)
        return func
    return real_bind

