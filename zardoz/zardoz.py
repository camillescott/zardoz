import dice

import discord
from discord.ext import commands

import rich
from rich.logging import RichHandler

import argparse
from enum import Enum
import json
import logging
import sys
import typing

from .zcrit import CritCommands
from .zhistory import HistoryCommands
from .zvars import VarCommands
from .state import Database, GameMode, ModeConvert, MODE_META
from .rolls import (RollHandler, QuietRollHandler, SekretRollHandler,
                    RollList, DiceDelta)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--auth', default='auth.json')
    parser.add_argument('--database', default='db.json')
    args = parser.parse_args()

    # Set up rich logging handler
    # (discord.py uses the python logger)
    logging.basicConfig(
        level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
    )
    log = logging.getLogger('discord')

    # parse authentication data
    with open(args.auth) as fp:
        auth = json.load(fp)
    try:
        TOKEN = auth['token']
    except:
        log.error('Must set "token" in auth.json!')
        sys.exit(1)
    else:
        log.info(f'TOKEN: {TOKEN}')

    # get a handle for the history database
    DB = Database(args.database)


    bot = commands.Bot(command_prefix='/')

    @bot.event
    async def on_ready():
        log.info(f'Ready: member of {bot.guilds}')
        log.info(f'Users: {bot.users}')
        DB.add_guilds(bot.guilds)

    @bot.command(name='z', help='Evaluate a dice roll.')
    async def zardoz_roll(ctx, *, args):

        try:
            roll = RollHandler(ctx, log, DB, args)
        except ValueError as e:
            log.error(f'Roll handling failed: {e}')
            await ctx.message.reply(f'You fucked up your roll, {ctx.author}. {e}')
        else:
            await ctx.message.reply(roll.msg())

    @bot.command(name='zq', help='Evaluate a dice roll, quietly.')
    async def zardoz_quiet_roll(ctx, *, args):

        try:
            roll = QuietRollHandler(ctx, log, DB, args)
        except ValueError as e:
            log.error(f'Roll handling failed: {e}')
            await ctx.message.reply(f'You fucked up your roll, {ctx.author}. {e}')
        else:
            await ctx.message.reply(roll.msg())

    @bot.command(name='zs', help='Make a secret roll and DM to member.')
    async def zardoz_secret_roll(ctx, member: typing.Optional[discord.Member], *, args):
        if member is None:
            member = ctx.author

        try:
            roll = SekretRollHandler(ctx, log, DB, args, require_tag=True)
        except ValueError as e:
            log.error(f'Roll handling failed: {e}')
            await ctx.author.send(f'You fucked up your roll, {ctx.author}. {e}')
        else:
            await member.send(roll.msg())

    #
    # Mode subcommands
    #

    @bot.group(name='zmode', help='Manage game modes for the server')
    async def zardoz_mode(ctx):
        if ctx.invoked_subcommand is None:
            pass
        log.info('CMD zmode')
    
    @zardoz_mode.command(name='set', help='Set the mode for the server.')
    async def zardoz_mode_set(ctx, mode: typing.Optional[ModeConvert]):
        if mode is None:
            mode = GameMode.DEFAULT
        DB.set_guild_mode(ctx.guild, mode)
        await ctx.send(f'**Set Mode:**: {GameMode(mode).name}')

    @zardoz_mode.command(name='get', help='Display the server mode.')
    async def zardoz_mode_get(ctx):
        current_mode = DB.get_guild_mode(ctx.guild)
        await ctx.send(f'**Mode:**: {GameMode(current_mode).name}\n'\
                       f'*{MODE_META[current_mode]}*')

    @zardoz_mode.command(name='list', help='List available modes.')
    async def zardoz_mode_list(ctx):
        modes = '\n'.join((f'{mode.name}: {MODE_META[mode]}' for mode in GameMode))
        await ctx.send(modes)

    #
    # Crit table subcommands
    #



    bot.add_cog(CritCommands(bot, DB))
    bot.add_cog(VarCommands(bot, DB))
    bot.add_cog(HistoryCommands(bot, DB))


    bot.run(TOKEN)


if __name__ == '__main__':
    main()
