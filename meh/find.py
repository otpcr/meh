# This file is placed in the Public Domain.
# pylint: disable=C,R,W0105,W0719,W0622,E1101,E0402


"locate objects"


import datetime
import json
import os
import pathlib
import time
import _thread


p = os.path.join


from .object  import Object, dumps, fqn, items, keys, loads, update
from .runtime import Cache


lock     = _thread.allocate_lock()
findlock = _thread.allocate_lock()


class Config:

    wdr = ""

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


def cdir(pth):
    path = pathlib.Path(pth)
    path.parent.mkdir(parents=True, exist_ok=True)


def fns(clz):
    dname = ''
    pth = store(clz)
    with lock:
        for rootdir, dirs, _files in os.walk(pth, topdown=False):
            if dirs:
                for dname in sorted(dirs):
                    if dname.count('-') == 2:
                        ddd = p(rootdir, dname)
                        for fll in os.listdir(ddd):
                            yield p(ddd, fll)


def find(clz, selector=None, index=None, deleted=False, matching=False):
    skel()
    nrs = -1
    pth = long(clz)
    with findlock:
        for fnm in sorted(fns(pth), key=fntime):
            obj = Cache.get(fnm)
            if obj:
                yield (fnm, obj)
                continue
            obj = Object()
            read(obj, fnm)
            if not deleted and '__deleted__' in dir(obj) and obj.__deleted__:
                continue
            if selector and not search(obj, selector, matching):
                continue
            nrs += 1
            if index is not None and nrs != int(index):
                continue
            Cache.add(fnm, obj)
            yield (fnm, obj)


def fntime(daystr):
    daystr = daystr.replace('_', ':')
    datestr = ' '.join(daystr.split(os.sep)[-2:])
    if '.' in datestr:
        datestr, rest = datestr.rsplit('.', 1)
    else:
        rest = ''
    timed = time.mktime(time.strptime(datestr, '%Y-%m-%d %H:%M:%S'))
    if rest:
        timed += float('.' + rest)
    return timed


def format(obj, args=None, skip=None, plain=False):
    if args is None:
        args = keys(obj)
    if skip is None:
        skip = []
    txt = ""
    for key in args:
        if key.startswith("__"):
            continue
        if key in skip:
            continue
        value = getattr(obj, key, None)
        if value is None:
            continue
        if plain:
            txt += f"{value} "
        elif isinstance(value, str) and len(value.split()) >= 2:
            txt += f'{key}="{value}" '
        else:
            txt += f'{key}={value} '
    return txt.strip()


def ident(obj):
    return p(fqn(obj), *str(datetime.datetime.now()).split())



def laps(seconds, short=True):
    txt = ""
    nsec = float(seconds)
    if nsec < 1:
        return f"{nsec:.2f}s"
    yea = 365*24*60*60
    week = 7*24*60*60
    nday = 24*60*60
    hour = 60*60
    minute = 60
    yeas = int(nsec/yea)
    nsec -= yeas*yea
    weeks = int(nsec/week)
    nsec -= weeks*week
    nrdays = int(nsec/nday)
    nsec -= nrdays*nday
    hours = int(nsec/hour)
    nsec -= hours*hour
    minutes = int(nsec/minute)
    nsec -= int(minute*minutes)
    sec = int(nsec)
    if yeas:
        txt += f"{yeas}y"
    if weeks:
        nrdays += weeks * 7
    if nrdays:
        txt += f"{nrdays}d"
    if short and txt:
        return txt.strip()
    if hours:
        txt += f"{hours}h"
    if minutes:
        txt += f"{minutes}m"
    if sec:
        txt += f"{sec}s"
    txt = txt.strip()
    return txt


def last(obj, selector=None):
    if selector is None:
        selector = {}
    result = sorted(
                    find(fqn(obj), selector),
                    key=lambda x: fntime(x[0])
                   )
    res = None
    if result:
        inp = result[-1]
        update(obj, inp[-1])
        res = inp[0]
    return res


def long(name):
    split = name.split(".")[-1].lower()
    res = name
    for names in types():
        if split == names.split(".")[-1].lower():
            res = names
            break
    return res


def match(obj, txt):
    for key in keys(obj):
        if txt in key:
            yield key


def read(obj, pth):
    with lock:
        with open(pth, 'r', encoding='utf-8') as ofile:
            try:
                obj2 = loads(ofile.read())
                update(obj, obj2)
            except json.decoder.JSONDecodeError as ex:
                raise Exception(pth) from ex
        return os.sep.join(pth.split(os.sep)[-3:])


def search(obj, selector, matching=None):
    res = False
    if not selector:
        return res
    for key, value in items(selector):
        val = getattr(obj, key, None)
        if not val:
            continue
        if matching and value == val:
            res = True
        elif str(value).lower() in str(val).lower():
            res = True
        else:
            res = False
            break
    return res


def skel():
    stor = p(Config.wdr, "store", "")
    path = pathlib.Path(stor)
    path.mkdir(parents=True, exist_ok=True)
    return path


def store(pth=""):
    return p(Config.wdr, "store", pth)


def strip(pth, nmr=3):
    return os.sep.join(pth.split(os.sep)[-nmr:])


def types():
    return os.listdir(store())


def write(obj, pth=None):
    with lock:
        if pth is None:
            pth = p(Config.wdr, "store", ident(obj))
        cdir(pth)
        txt = dumps(obj, indent=4)
        with open(pth, 'w', encoding='utf-8') as ofile:
            ofile.write(txt)
        return pth
