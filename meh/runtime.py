# This file is placed in the Public Domain.
# pylint: disable=C,R,W0105,W0212,W0621,W0718


"runtime"


import inspect
import queue
import threading
import time
import traceback
import types
import _thread


"cache"


class Cache:

    objs = {}

    @staticmethod
    def add(path, obj):
        with cachelock:
            Cache.objs[path] = obj

    @staticmethod
    def get(path):
        with cachelock:
            return Cache.objs.get(path)

    @staticmethod
    def typed(matcher):
        with cachelock:
            for key in Cache.objs:
                if matcher not in key:
                    continue
                yield Cache.objs.get(key)


"commands"


class Commands:

    cmds = {}

    @staticmethod
    def add(func):
        Commands.cmds[func.__name__] = func

    @staticmethod
    def scan(mod):
        for key, cmdz in inspect.getmembers(mod, inspect.isfunction):
            if key.startswith("cb"):
                continue
            if 'event' in cmdz.__code__.co_varnames:
                Commands.add(cmdz)


def command(bot, evt):
    parse(evt, evt.txt)
    if "ident" in dir(bot):
        evt.orig = bot.ident
    func = Commands.cmds.get(evt.cmd, None)
    if not func:
        evt.ready()
        return
    try:
        func(evt)
    except Exception as ex:
        later(ex)
    evt.ready()


def modloop(*pkgs, disable=""):
    for pkg in pkgs:
        for modname in dir(pkg):
            if modname in spl(disable):
                continue
            if modname.startswith("__"):
                continue
            yield getattr(pkg, modname)


def scan(*pkgs, init=False, disable=""):
    result = []
    for mod in modloop(*pkgs, disable=disable):
        if type(mod) is not types.ModuleType:
            continue
        Commands.scan(mod)
        thr = None
        if init and "init" in dir(mod):
            thr = launch(mod.init)
        result.append((mod, thr))
    return result


def spl(txt):
    try:
        result = txt.split(',')
    except (TypeError, ValueError):
        result = txt
    return [x for x in result if x]


"default"


class Default:

    def __contains__(self, key):
        return key in dir(self)

    def __getattr__(self, key):
        return self.__dict__.get(key, "")

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


"config"


class Config(Default):

    pass


"errors"


class Errors:

    errors = []

    @staticmethod
    def format(exc):
        return traceback.format_exception(
            type(exc),
            exc,
            exc.__traceback__
        )


def errors():
    for err in Errors.errors:
        for line in err:
            yield line


def later(exc):
    excp = exc.with_traceback(exc.__traceback__)
    fmt = Errors.format(excp)
    if fmt not in Errors.errors:
        Errors.errors.append(fmt)


"event"


class Event:

    def __init__(self):
        self._ready = threading.Event()
        self._thr   = None
        self.result = []
        self.type   = "event"
        self.txt    = ""

    def __getattr__(self, key):
        return self.__dict__.get(key, "")

    def __str__(self):
        return str(self.__dict__)

    def ready(self):
        self._ready.set()

    def reply(self, txt):
        self.result.append(txt)

    def wait(self):
        self._ready.wait()
        if self._thr:
            self._thr.join()


"reactor"


class Reactor:

    def __init__(self):
        self.cbs = {}
        self.queue = queue.Queue()
        self.stopped = threading.Event()

    def callback(self, evt):
        func = self.cbs.get(evt.type, None)
        if not func:
            evt.ready()
            return
        try:
            evt._thr = launch(func, self, evt)
        except Exception as ex:
            evt._ex = ex
            later(ex)
            evt.ready()

    def display(self, evt):
        for txt in evt.result:
            self.raw(txt)

    def loop(self):
        while not self.stopped.is_set():
            try:
                evt = self.poll()
                if not self.stopped.is_set():
                    self.callback(evt)
            except (KeyboardInterrupt, EOFError):
                if "ready" in dir(evt):
                    evt.ready()
                _thread.interrupt_main()
                
    def poll(self):
        if not self.stopped.is_set():
            return self.queue.get()

    def put(self, evt):
        self.queue.put(evt)

    def raw(self, txt):
        raise NotImplementedError("raw")

    def register(self, typ, cbs):
        self.cbs[typ] = cbs

    def start(self):
        launch(self.loop)

    def stop(self):
        self.stopped.set()


class Client(Reactor):

    def __init__(self):
        Reactor.__init__(self)
        self.register("command", command)

    def raw(self):
        raise NotImplementedError("raw")


"threads"


class Thread(threading.Thread):

    def __init__(self, func, thrname, *args, daemon=True, **kwargs):
        super().__init__(None, self.run, thrname, (), {}, daemon=daemon)
        self.name = thrname or name(func)
        self.queue = queue.Queue()
        self.result = None
        self.starttime = time.time()
        self.queue.put_nowait((func, args))

    def __contains__(self, key):
        return key in self.__dict__

    def __iter__(self):
        return self

    def __next__(self):
        yield from dir(self)

    def size(self):
        return self.queue.qsize()

    def join(self, timeout=None):
        super().join(timeout)
        return self.result

    def run(self):
        try:
            func, args = self.queue.get()
            self.result = func(*args)
        except (KeyboardInterrupt, EOFError):
            _thread.interrupt_main()
        except Exception as ex:
            later(ex)


def launch(func, *args, **kwargs):
    nme = kwargs.get("name", name(func))
    thread = Thread(func, nme, *args, **kwargs)
    thread.start()
    return thread


def name(obj):
    typ = type(obj)
    if '__builtins__' in dir(typ):
        return obj.__name__
    if '__self__' in dir(obj):
        return f'{obj.__self__.__class__.__name__}.{obj.__name__}'
    if '__class__' in dir(obj) and '__name__' in dir(obj):
        return f'{obj.__class__.__name__}.{obj.__name__}'
    if '__class__' in dir(obj):
        return f"{obj.__class__.__module__}.{obj.__class__.__name__}"
    if '__name__' in dir(obj):
        return f'{obj.__class__.__name__}.{obj.__name__}'
    return None


"timers"


class Timer:

    def __init__(self, sleep, func, *args, thrname=None, **kwargs):
        self.args  = args
        self.func  = func
        self.kwargs = kwargs
        self.sleep = sleep
        self.name  = thrname or kwargs.get("name", name(func))
        self.state = {}
        self.timer = None

    def run(self):
        self.state["latest"] = time.time()
        launch(self.func, *self.args)

    def start(self):
        timer = threading.Timer(self.sleep, self.run)
        timer.name   = self.name
        timer.sleep  = self.sleep
        timer.state  = self.state
        timer.func   = self.func
        timer.state["starttime"] = time.time()
        timer.state["latest"]    = time.time()
        timer.start()
        self.timer   = timer

    def stop(self):
        if self.timer:
            self.timer.cancel()


class Repeater(Timer):

    def run(self):
        launch(self.start)
        super().run()


"utilities"


def parse(obj, txt=None):
    if txt is None:
        txt = ""
    args = []
    obj.args    = []
    obj.cmd     = ""
    obj.gets    = Default()
    obj.hasmods = False
    obj.index   = None
    obj.mod     = ""
    obj.opts    = ""
    obj.result  = []
    obj.sets    = Default()
    obj.txt     = txt or ""
    obj.otxt    = obj.txt
    _nr = -1
    for spli in obj.otxt.split():
        if spli.startswith("-"):
            try:
                obj.index = int(spli[1:])
            except ValueError:
                obj.opts += spli[1:]
            continue
        if "==" in spli:
            key, value = spli.split("==", maxsplit=1)
            val = getattr(obj.gets, key, None)
            if val:
                value = val + "," + value
                setattr(obj.gets, key, value)
            continue
        if "=" in spli:
            key, value = spli.split("=", maxsplit=1)
            if key == "mod":
                obj.hasmods = True
                if obj.mod:
                    obj.mod += f",{value}"
                else:
                    obj.mod = value
                continue
            setattr(obj.sets, key, value)
            continue
        _nr += 1
        if _nr == 0:
            obj.cmd = spli
            continue
        args.append(spli)
    if args:
        obj.args = args
        obj.txt  = obj.cmd or ""
        obj.rest = " ".join(obj.args)
        obj.txt  = obj.cmd + " " + obj.rest
    else:
        obj.txt = obj.cmd or ""
    return obj


"interface"


def __dir__():
    return (
        'Cache',
        'Client',
        'Commands',
        'Config',
        'Default',
        'Errors',
        'Event',
        'Reactor',
        'Repeater',
        'Thread',
        'Timer',
        'command',
        'errors',
        'later',
        'launch',
        'scan'
    )
