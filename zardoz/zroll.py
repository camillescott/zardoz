#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2020
# File   : zroll.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 22.02.2021

import typing

import discord
from discord.ext import commands

from .database import fetch_guild_db
from .logging import LoggingMixin
from .rolls import (RollHandler, QuietRollHandler, SekretRollHandler, RerollHandler,
                    RollList, DiceDelta, tokenize_roll)
from .utils import handle_http_exception


class RollCommands(commands.Cog, LoggingMixin):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

        super().__init__()

    @commands.command(name='z', help='Evaluate a dice roll.')
    @fetch_guild_db
    @handle_http_exception
    async def zardoz_roll(self, ctx, *, args):

        try:
            roll = RollHandler(ctx, self.log, ctx.variables, args,
                               game_mode=ctx.game_mode)
        except ValueError as e:
            self.log.error(f'Roll handling failed: {e}')
            await ctx.message.reply(f'You fucked up your roll, {ctx.author}. {e}')
        else:
            await roll.add_to_db(ctx.guild_db)
            await ctx.message.reply(roll.msg())

    @commands.command(name='zq', help='Evaluate a dice roll, quietly.')
    @fetch_guild_db
    @handle_http_exception
    async def zardoz_quiet_roll(self, ctx, *, args):

        try:
            roll = QuietRollHandler(ctx, self.log, ctx.variables, args,
                                    game_mode=ctx.game_mode)
        except ValueError as e:
            self.log.error(f'Roll handling failed: {e}')
            await ctx.message.reply(f'You fucked up your roll, {ctx.author}. {e}')
        else:
            await roll.add_to_db(ctx.guild_db)
            await ctx.message.reply(roll.msg())

    @commands.command(name='zs', help='Make a secret roll and DM to member.')
    @fetch_guild_db
    @handle_http_exception
    async def zardoz_secret_roll(self, ctx, member: typing.Optional[discord.Member], *, args):
        if member is None:
            member = ctx.author

        try:
            roll = SekretRollHandler(ctx, self.log, ctx.variables, args,
                                     game_mode=ctx.game_mode, require_tag=True)
        except ValueError as e:
            self.log.error(f'Roll handling failed: {e}')
            await ctx.author.send(f'You fucked up your roll, {ctx.author}. {e}')
        else:
            await roll.add_to_db(ctx.guild_db)
            await member.send(roll.msg())

    @commands.command(name='zr', help='Reroll previous roll')
    @fetch_guild_db
    @handle_http_exception
    async def zroll_reroll(self, ctx, member: typing.Optional[discord.Member], *, args=''):
        if member is None:
            member = ctx.author

        saved = await ctx.guild_db.get_last_user_roll(member.id)

        if saved is None:
            await ctx.message.reply(f'Ope, no roll history for {member}.')
        else:
            cmd = saved['roll']
            _, tag = tokenize_roll(args)
            if not tag:
                tag = saved['tag']
            tag = '# ' + tag

            roll = RerollHandler(ctx, self.log, ctx.variables, cmd + tag,
                                 game_mode=ctx.game_mode)

            if member == ctx.author:
                target = 'self'
            else:
                target = member.nick if member.nick else member.name

            await roll.add_to_db(ctx.guild_db)
            await ctx.message.reply(f'Reroll {roll.msg(target)}')
