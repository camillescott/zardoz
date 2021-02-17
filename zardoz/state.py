from datetime import datetime
from enum import IntEnum, auto

from discord.ext import commands
from tinydb import TinyDB, Query, where


class GameMode(IntEnum):
    DEFAULT = auto()
    RT = auto()
    DND = auto()
    AW = auto()


MODE_META = {GameMode.DEFAULT: 'Default die is 1d6',
             GameMode.RT: 'Default die is 1d100; reports DoS/DoF',
             GameMode.DND: 'Default die is 1d20',
             GameMode.AW: 'Default die is 1d6'}


MODE_DICE = {GameMode.DEFAULT: '1d6',
             GameMode.RT: '1d100',
             GameMode.DND: '1d20',
             GameMode.AW: '1d6'}

