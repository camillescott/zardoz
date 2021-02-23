#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2020
# File   : zmode.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 22.02.2021

import typing

from discord.ext import commands

from .database import fetch_guild_db
from .logging import LoggingMixin
from .state import GameMode, MODE_META


class ModeConvert(commands.Converter):

    async def convert(self, ctx, argument):
        try:
            converted = GameMode[argument]
        except KeyError:
            raise commands.BadArgument(f'{argument} is not a valid mode.')
        return converted


class ModeCommands(commands.Cog, LoggingMixin):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

        super().__init__()

    @commands.group(name='zmode', help='Manage game modes for the server')
    @fetch_guild_db
    async def zmode(self, ctx, mode: typing.Optional[ModeConvert]):
        if ctx.invoked_subcommand is not None:
            return

        if mode is None:
            current_mode = await ctx.guild_db.get_guild_mode()
            await ctx.send(f'**Mode:**: {GameMode(current_mode).name}\n'\
                           f'*{MODE_META[current_mode]}*')
        else:
            try:
                await ctx.guild_db.set_guild_mode(mode)
            except ValueError as e:
                await ctx.message.reply(f'{e}')
            else:
                await ctx.message.reply(f'**Set Mode:** {GameMode(mode).name}')
    
    @zmode.command(name='list', help='List available modes.')
    async def zmode_list(self, ctx):
        modes = '\n'.join((f'{mode.name}: {MODE_META[mode]}' for mode in GameMode))
        await ctx.message.reply(modes)

