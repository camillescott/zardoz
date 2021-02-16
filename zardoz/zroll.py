import typing

import discord
from discord.ext import commands

from .logging import LoggingMixin
from .rolls import (RollHandler, QuietRollHandler, SekretRollHandler,
                    RollList, DiceDelta)


class RollCommands(commands.Cog, LoggingMixin):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

        super().__init__()

    @commands.command(name='z', help='Evaluate a dice roll.')
    async def zardoz_roll(self, ctx, *, args):

        try:
            roll = RollHandler(ctx, self.log, self.db, args)
        except ValueError as e:
            self.log.error(f'Roll handling failed: {e}')
            await ctx.message.reply(f'You fucked up your roll, {ctx.author}. {e}')
        else:
            await ctx.message.reply(roll.msg())

    @commands.command(name='zq', help='Evaluate a dice roll, quietly.')
    async def zardoz_quiet_roll(self, ctx, *, args):

        try:
            roll = QuietRollHandler(ctx, self.log, self.db, args)
        except ValueError as e:
            self.log.error(f'Roll handling failed: {e}')
            await ctx.message.reply(f'You fucked up your roll, {ctx.author}. {e}')
        else:
            await ctx.message.reply(roll.msg())

    @commands.command(name='zs', help='Make a secret roll and DM to member.')
    async def zardoz_secret_roll(self, ctx, member: typing.Optional[discord.Member], *, args):
        if member is None:
            member = ctx.author

        try:
            roll = SekretRollHandler(ctx, self.log, self.db, args, require_tag=True)
        except ValueError as e:
            self.log.error(f'Roll handling failed: {e}')
            await ctx.author.send(f'You fucked up your roll, {ctx.author}. {e}')
        else:
            await member.send(roll.msg())

