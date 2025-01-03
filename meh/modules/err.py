# This file is placed in the Public Domain.
# pylint: disable=C,E0402


"errors"


from ..runtime import Errors


def err(event):
    nmr = 0
    for exc in Errors.errors:
        for line in exc:
            event.reply(line.strip())
        nmr += 1
    if not nmr:
        event.reply("no errors")
        return
    event.reply(f"found {nmr} errors.")
