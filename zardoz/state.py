#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2020
# File   : state.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 22.02.2021

from datetime import datetime
from enum import IntEnum, auto

from discord.ext import commands


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

