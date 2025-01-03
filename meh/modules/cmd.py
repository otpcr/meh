# This file is placed in the Public Domain.
# pylint: disable=C,E0402


"commands"


from ..runtime import Commands


def cmd(event):
    event.reply(",".join(sorted(Commands.cmds.keys())))
