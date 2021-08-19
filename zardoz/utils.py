#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2020
# File   : utils.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 22.02.2021

import argparse
from dataclasses import is_dataclass
from datetime import datetime
import functools
import os
from pathlib import Path
import random

import discord
from xdg import xdg_data_home


ZARDOZ_PKG_DIR = os.path.abspath(os.path.dirname(__file__))
__time_format__ = '%a %b %d %I:%M%p %Z'

FAILURE = 'F 🛇'
SUCCESS = 'S ✅'


def d10():
    return random.randint(1, 10)


def d100():
    return random.randint(1, 100)


def Nd10(n=1):
    return [random.randint(1,10) for _ in range(n)]


def Nd100(n=1):
    return [random.randint(1,100)  for _ in range(n)]


def default_database_dir(debug=False):
    if not debug:
        return xdg_data_home().joinpath('zardoz-bot', 'databases')
    else:
        return xdg_data_home().joinpath('zardoz-bot', 'debug', 'databases')


def default_log_file(debug=False):
    if not debug:
        return xdg_data_home().joinpath('zardoz-bot', 'bot.log')
    else:
        return xdg_data_home().joinpath('zardoz-bot', 'debug', 'bot.log')


def reverse_number(num: int):
    result = 0
    while (num > 0):
        result = (num * 10) + (num % 10)
        num = num // 10
    return result


def handle_http_exception(func):

    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        try:
            return await func(self, ctx, *args, **kwargs)
        except discord.HTTPException:
            await ctx.message.reply('Hey broh, that\'s a big response.'\
                                    ' Try dialing back your request,'\
                                    ' I\'m only human.')
            raise
    return wrapper

