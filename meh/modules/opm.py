# This file is placed in the Public Domain.
# pylint: disable=C,W0105,E0402


"OPML"


import os
import uuid
import _thread


from ..find    import find, write
from ..object  import Object, update
from  .rss     import Rss
from ..runtime import spl


importlock = _thread.allocate_lock()
skipped    = []


TEMPLATE = """<opml version="1.0">
    <head>
        <title>OPML</title>
    </head>
    <body>
        <outline title="opml" text="rss feeds">"""


class OPMLParser:

    @staticmethod
    def getnames(line):
        return [x.split('="')[0]  for x in line.split()]

    @staticmethod
    def getvalue(line, attr):
        lne = ''
        index1 = line.find(f'{attr}="')
        if index1 == -1:
            return lne
        index1 += len(attr) + 2
        index2 = line.find('"', index1)
        if index2 == -1:
            index2 = line.find('/>', index1)
        if index2 == -1:
            return lne
        lne = line[index1:index2]
        if 'CDATA' in lne:
            lne = lne.replace('![CDATA[', '')
            lne = lne.replace(']]', '')
            #lne = lne[1:-1]
        return lne

    @staticmethod
    def getattrs(line, token):
        index = 0
        result = []
        stop = False
        while not stop:
            index1 = line.find(f'<{token} ', index)
            if index1 == -1:
                return result
            index1 += len(token) + 2
            index2 = line.find('/>', index1)
            if index2 == -1:
                return result
            result.append(line[index1:index2])
            index = index2
        return result

    @staticmethod
    def parse(txt, toke="outline", itemz=None):
        if itemz is None:
            itemz = ",".join(OPMLParser.getnames(txt))
        result = []
        for attrz in OPMLParser.getattrs(txt, toke):
            if not attrz:
                continue
            obj = Object()
            for itm in spl(itemz):
                if itm == "link":
                    itm = "href"
                val = OPMLParser.getvalue(attrz, itm)
                if not val:
                    continue
                if itm == "href":
                    itm = "link"
                setattr(obj, itm, val.strip())
            result.append(obj)
        return result


"utilities"


def attrs(obj, txt):
    update(obj, OPMLParser.parse(txt))


def shortid():
    return str(uuid.uuid4())[:8]


"commands"


def exp(event):
    event.reply(TEMPLATE)
    nrs = 0
    for _fn, ooo in find("rss"):
        nrs += 1
        obj = Rss()
        update(obj, ooo)
        name = f"url{nrs}"
        txt = f'<outline name="{name}" display_list="{obj.display_list}" xmlUrl="{obj.rss}"/>'
        event.reply(" "*12 + txt)
    event.reply(" "*8 + "</outline>")
    event.reply("    <body>")
    event.reply("</opml>")


def imp(event):
    if not event.args:
        event.reply("imp <filename>")
        return
    fnm = event.args[0]
    if not os.path.exists(fnm):
        event.reply(f"no {fnm} file found.")
        return
    with open(fnm, "r", encoding="utf-8") as file:
        txt = file.read()
    prs = OPMLParser()
    nrs = 0
    nrskip = 0
    insertid = shortid()
    with importlock:
        for obj in prs.parse(txt, 'outline', "name,display_list,xmlUrl"):
            url = obj.xmlUrl
            if url in skipped:
                continue
            if not url.startswith("http"):
                continue
            has = list(find("rss", {'rss': url}, matching=True))
            if has:
                skipped.append(url)
                nrskip += 1
                continue
            feed = Rss()
            update(feed, obj)
            feed.rss = obj.xmlUrl
            feed.insertid = insertid
            write(feed)
            nrs += 1
    if nrskip:
        event.reply(f"skipped {nrskip} urls.")
    if nrs:
        event.reply(f"added {nrs} urls.")
