# This file is placed in the Public Domain.
# pylint: disable=C0116,E0402


"uptime"


import time


from ..find import laps


STARTTIME = time.time()


def upt(event):
    event.reply(laps(time.time()-STARTTIME))
