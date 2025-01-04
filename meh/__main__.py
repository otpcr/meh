# This file is placed in the Public Domain.
# pylint: disable=C,R0903,W0212,W0611,W0718,E0402


"main"


import os
import pathlib
import sys
import time
import _thread


from .find    import Config
from .modules import face
from .runtime import Client, Commands, Event
from .runtime import command, errors, later, parse, scan


Config.name = Config.__module__.split(".", maxsplit=2)[-2]
Config.wdr  = os.path.expanduser(f"~/.{Config.name}")


TXT = """[Unit]
Description=%s
After=network-online.target

[Service]
Type=simple
User=%s
Group=%s
ExecStart=/home/%s/.local/bin/%s -s

[Install]
WantedBy=multi-user.target"""


cfg = Config()
p   = os.path.join


class CLI(Client):

    def raw(self, txt):
        print(txt)


class Console(CLI):

    def announce(self, txt):
        self.raw(txt)

    def callback(self, evt):
        CLI.callback(self, evt)
        evt.wait()
        self.display(evt)

    def poll(self):
        evt = Event()
        evt.txt = input("> ")
        evt.type = "command"
        return evt


def banner():
    tme = time.ctime(time.time()).replace("  ", " ")
    print(f"{cfg.name.upper()} since {tme}")


def background():
    daemon(True)
    privileges()
    pidfile(pidname(Config.name))
    scan(face, init=True)
    forever()


def check(txt):
    args = sys.argv[1:]
    for arg in args:
        if not arg.startswith("-"):
            continue
        for c in txt:
            if c in arg:
                return True
    return False


def console():
    import readline
    parse(cfg, " ".join(sys.argv[1:]))
    if "v" in cfg.opts:
        banner()
    for mod, thr in scan(face, init="i" in cfg.opts, disable=cfg.sets.dis):
        if "v" in cfg.opts and "output" in dir(mod):
            mod.output = print
        if thr and "w" in cfg.opts:
            thr.join()
    csl = Console()
    csl.start()
    forever()


def control():
    Commands.add(srv)
    parse(cfg, " ".join(sys.argv[1:]))
    if not cfg.otxt:
        return
    scan(face)
    evt = Event()
    evt.type = "command"
    evt.txt = cfg.otxt
    csl = CLI()
    command(csl, evt)
    csl.display(evt)
    evt.wait()


def daemon(verbose=False):
    pid = os.fork()
    if pid != 0:
        os._exit(0)
    os.setsid()
    pid2 = os.fork()
    if pid2 != 0:
        os._exit(0)
    if not verbose:
        with open('/dev/null', 'r', encoding="utf-8") as sis:
            os.dup2(sis.fileno(), sys.stdin.fileno())
        with open('/dev/null', 'a+', encoding="utf-8") as sos:
            os.dup2(sos.fileno(), sys.stdout.fileno())
        with open('/dev/null', 'a+', encoding="utf-8") as ses:
            os.dup2(ses.fileno(), sys.stderr.fileno())
    os.umask(0)
    os.chdir("/")
    os.nice(10)


def forever():
    while True:
        try:
            time.sleep(0.1)
        except (KeyboardInterrupt, EOFError):
            _thread.interrupt_main()


def pidfile(filename):
    if os.path.exists(filename):
        os.unlink(filename)
    path2 = pathlib.Path(filename)
    path2.parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as fds:
        fds.write(str(os.getpid()))


def pidname(name):
    return p(Config.wdr, f"{name}.pid")


def privileges():
    import getpass
    import pwd
    pwnam2 = pwd.getpwnam(getpass.getuser())
    os.setgid(pwnam2.pw_gid)
    os.setuid(pwnam2.pw_uid)


def service():
    privileges()
    pidfile(pidname(Config.name))
    scan(face, init=True)
    forever()


def wraps():
    wrap(service)


def srv(event):
    import getpass
    name = getpass.getuser()
    event.reply(TXT % (Config.name.upper(), name, name, name, Config.name))


def wrap(func):
    import termios
    old = None
    try:
        old = termios.tcgetattr(sys.stdin.fileno())
    except termios.error:
        pass
    try:
        func()
    except (KeyboardInterrupt, EOFError):
        print("")
    except Exception as exc:
        later(exc)
    finally:
        if old:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old)
    for line in errors():
        print(line)


def wrapped():
    wrap(main)


def main():
    if check("c"):
        wrap(console)
    elif check("d"):
        background()
    elif check("s"):
        wrap(service)
    else:
        control()


if __name__ == "__main__":
    wrapped()
