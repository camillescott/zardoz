#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : zsample.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 19.03.2021

import random
import typing

import discord
from discord.ext import commands

from ..database import fetch_guild_db
from ..logging import LoggingMixin
from ..rolls import tokenize_roll
from ..utils import handle_http_exception


class SampleCommands(commands.Cog, LoggingMixin):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

        super().__init__()

    @commands.command(name='sample')
    @fetch_guild_db
    @handle_http_exception
    async def sample(self, ctx, k: int, N: int, *, args=''):
        '''
        Sample integers from discreet distributions.
        '''
        try:
            if k < 1 or N < 1:
                raise ValueError('`k` and `N` must be greater than 1!')
            if k > N:
                raise ValueError('`k` (sample size) cannot be greater than `N`!')
            if N > 100:
                raise ValueError(f'`N`={N} too large! Try 100 or less dawg.')
        except ValueError as e:
            await ctx.message.reply(f'I dun wan it: {e}')
            return

        pop = list(range(1, N+1))
        sample = sorted(random.sample(pop, k))
        roll, tag = tokenize_roll(args)

        header = f':question: {ctx.author.mention}' + (f': *{tag}*' if tag else '')
        action = f'Sample **{k}** from *[1..{N}]*'
        result = f'***Result:***\n```{sample}```'
        msg = '\n'.join([header, action, result])

        await ctx.message.reply(msg)

