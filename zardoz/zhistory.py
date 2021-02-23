#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2020
# File   : zhistory.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 22.02.2021

import typing

import discord
from discord.ext import commands

from .database import fetch_guild_db
from .logging import LoggingMixin
from .utils import __time_format__


class HistoryCommands(commands.Cog, LoggingMixin):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db 

        super().__init__()

    @commands.command(name='zhist', help='Display roll history.')
    @fetch_guild_db
    async def zhist(self, ctx, member: typing.Optional[discord.Member],
                               max_rolls: typing.Optional[int] = 5):

        records = [r async for r in ctx.guild_db.get_rolls(max_rolls=max_rolls)]

        def format(row):
            name = row.get('member_nick', None)
            if name is None:
                name = row.get('member_name', row.get('member_nick', 'Unknown'))
            timestamp = row['time'].strftime(__time_format__)
            return f'{name} @ `{timestamp}`: `{row["roll"]:20}` ⟿  `{row["result"]}`'

        msg = '\n'.join((format(record) for record in records))
        await ctx.send(f'**Roll :game_die: History**:\n{msg}')


