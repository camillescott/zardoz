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

from ..database import fetch_guild_db
from ..logging import LoggingMixin
from ..utils import __time_format__


class HistoryCommands(commands.Cog, LoggingMixin):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db 

        super().__init__()

    @commands.command(name='hist', aliases=['history'])
    @fetch_guild_db
    async def history(self, ctx, member: typing.Optional[discord.Member],
                               max_rolls: typing.Optional[int] = 5):
        '''
        Display the roll history for the given member, or for the server
        if a member is not specified.
        '''

        records = [r async for r in ctx.guild_db.get_rolls(max_rolls=max_rolls)]

        def format(row):
            name = row.get('member_nick', None)
            if name is None:
                name = row.get('member_name', row.get('member_nick', 'Unknown'))
            timestamp = row['time'].strftime(__time_format__)
            result = f'{name} @ `{timestamp}`: `{row["roll"]:20}` ⟿  `{row["result"]}`'
            if row['tag']:
                result += f'# {row["tag"]}'
            return result

        msg = '\n'.join((format(record) for record in records))
        await ctx.send(f'**Roll :game_die: History**:\n{msg}')


