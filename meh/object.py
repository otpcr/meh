# This file is placed in the Public Domain.
# pylint: disable=C,R,W0105,W0719,W0622,E1101


"a clean namespace"


import datetime
import json
import os
import pathlib
import time
import _thread


lock      = _thread.allocate_lock()
cachelock = _thread.allocate_lock()
findlock  = _thread.allocate_lock()
p         = os.path.join


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


"object"


class Object:

    def __str__(self):
        return str(self.__dict__)


"decoder"


class Decoder(json.JSONDecoder):

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, *args, **kwargs)

    def decode(self, s, _w=None):
        val = json.JSONDecoder.decode(self, s)
        if val is None:
            val = {}
        return val

    def raw_decode(self, s, idx=0):
        return json.JSONDecoder.raw_decode(self, s, idx)


def hook(data):
    obj = Object()
    construct(obj, data)
    return obj


def loads(string, *args, **kw):
    kw["cls"] = Decoder
    kw["object_hook"] = hook
    return json.loads(string, *args, **kw)


"encoder"


class Encoder(json.JSONEncoder):

    def __init__(self, *args, **kwargs):
        json.JSONEncoder.__init__(self, *args, **kwargs)

    def default(self, o):
        try:
            return o.items()
        except AttributeError:
            pass
        try:
            return vars(o)
        except ValueError:
            pass
        try:
            return iter(o)
        except ValueError:
            pass
        return json.JSONEncoder.default(self, o)

    def encode(self, o) -> str:
        return json.JSONEncoder.encode(self, o)

    def iterencode(self, o, _one_shot=False):
        return json.JSONEncoder.iterencode(self, o, _one_shot)


def dumps(*args, **kw):
    kw["cls"] = Encoder
    return json.dumps(*args, **kw)


"methods"


def construct(obj, *args, **kwargs):
    if args:
        val = args[0]
        try:
            update(obj, vars(val))
        except TypeError:
            try:
                update(obj, val)
            except ValueError:
                update(obj, dict(val))
    if kwargs:
        update(obj, kwargs)


def edit(obj, setter, skip=False):
    for key, val in items(setter):
        if skip and val == "":
            continue
        try:
            setattr(obj, key, int(val))
            continue
        except ValueError:
            pass
        try:
            setattr(obj, key, float(val))
            continue
        except ValueError:
            pass
        if val in ["True", "true"]:
            setattr(obj, key, True)
        elif val in ["False", "false"]:
            setattr(obj, key, False)
        else:
            setattr(obj, key, val)


def fqn(obj):
    kin = str(type(obj)).split()[-1][1:-2]
    if kin == "type":
        kin = f"{obj.__module__}.{obj.__name__}"
    return kin


def items(obj):
    if isinstance(obj,type({})):
        return obj.items()
    return obj.__dict__.items()


def keys(obj):
    if isinstance(obj, type({})):
        return obj.keys()
    return list(obj.__dict__.keys())


def update(obj, data):
    if isinstance(data, type({})):
        obj.__dict__.update(data)
    else:
        obj.__dict__.update(vars(data))


def values(obj):
    return obj.__dict__.values()


"disk"


def cdir(pth):
    path = pathlib.Path(pth)
    path.parent.mkdir(parents=True, exist_ok=True)



def fns(pth):
    dname = ''
    with lock:
        for rootdir, dirs, _files in os.walk(pth, topdown=False):
            if dirs:
                for dname in sorted(dirs):
                    if dname.count('-') == 2:
                        ddd = p(rootdir, dname)
                        for fll in os.scandir(ddd):
                            yield strip(p(ddd, fll))


def find(pth, selector=None, index=None, deleted=False, matching=False):
    nrs = -1
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



def ident(obj):
    return p(fqn(obj), *str(datetime.datetime.now()).split())


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


def strip(pth, nmr=3):
    return os.sep.join(pth.split(os.sep)[-nmr:])


def write(obj, pth=None):
    with lock:
        if pth is None:
            pth = ident(obj)
        cdir(pth)
        txt = dumps(obj, indent=4)
        with open(pth, 'w', encoding='utf-8') as ofile:
            ofile.write(txt)
        return pth


"interface"


def __dir__():
    return (
        'Object',
        'construct',
        'edit',
        'find',
        'fqn',
        'keys',
        'last',
        'items',
        'values',
        'update'
    )
