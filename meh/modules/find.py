# This file is placed in the Public Domain.
# pylint: disable=C,R,W0105,W0719,W0622,E1101,E0402


"locate objects"


import os
import time
import _thread


p = os.path.join


from ..object  import Config, Object, fqn, items, lock, read, update
from ..runtime import Cache


findlock = _thread.allocate_lock()


def fns(pth):
    dname = ''
    with lock:
        for rootdir, dirs, _files in os.walk(pth, topdown=False):
            if dirs:
                for dname in sorted(dirs):
                    if dname.count('-') == 2:
                        ddd = p(rootdir, dname)
                        for fll in os.scandir(ddd):
                            yield p(ddd, fll)


def find(clz, selector=None, index=None, deleted=False, matching=False):
    nrs = -1
    pth = store(long(clz))
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


def store(pth=""):
    return p(Config.wdr, "store", pth)


def strip(pth, nmr=3):
    return os.sep.join(pth.split(os.sep)[-nmr:])


def types():
    return os.listdir(store())
