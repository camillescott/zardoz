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

from .crit import load_crit_tables
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
    CRITS = load_crit_tables(log)
    log.info(f'Loaded crits: {CRITS}')

    bot = commands.Bot(command_prefix='/')

    @bot.event
    async def on_ready():
        log.info(f'Ready: member of {bot.guilds}')
        log.info(f'Users: {bot.users}')
        DB.add_guilds(bot.guilds)

    @bot.command(name='z', help='Evaluate a dice roll.')
    async def zardoz_roll(ctx, *args):

        try:
            roll = RollHandler(ctx, log, DB, args)
        except ValueError as e:
            log.error(f'Roll handling failed: {e}')
            await ctx.message.reply(f'You fucked up your roll, {ctx.author}. {e}')
        else:
            await ctx.message.reply(roll.msg())

    @bot.command(name='zq', help='Evaluate a dice roll, quietly.')
    async def zardoz_quiet_roll(ctx, *args):

        try:
            roll = QuietRollHandler(ctx, log, DB, args)
        except ValueError as e:
            log.error(f'Roll handling failed: {e}')
            await ctx.message.reply(f'You fucked up your roll, {ctx.author}. {e}')
        else:
            await ctx.message.reply(roll.msg())

    @bot.command(name='zs', help='Make a secret roll and DM to member.')
    async def zardoz_secret_roll(ctx, member: typing.Optional[discord.Member], *args):
        if member is None:
            member = ctx.author

        try:
            roll = SekretRollHandler(ctx, log, DB, args, require_tag=True)
        except ValueError as e:
            log.error(f'Roll handling failed: {e}')
            await ctx.author.send(f'You fucked up your roll, {ctx.author}. {e}')
        else:
            await member.send(roll.msg())

    @bot.command(name='zhist', help='Display roll history.')
    async def zardoz_history(ctx, max_elems: typing.Optional[int] = -1):
        log.info(f'CMD zhist {max_elems}.')

        guild_hist = DB.query_guild_rolls(ctx.guild)
        if max_elems > 0:
            guild_hist = guild_hist[-max_elems:]

        records = []
        for row in guild_hist:
            name = row.get('member_nick', None)
            if name is None:
                name = row.get('member_name', row.get('member_nick', 'Unknown'))
            records.append(f'{name}: {row["expr"]} ⟿  {row["result"]}')

        guild_hist = '\n'.join(records)
        await ctx.send(f'Roll History:\n{guild_hist}')

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
    # Variable subcommands
    #

    @bot.group(name='zvar', help='Manage variables for the server.')
    async def zardoz_var(ctx):
        if ctx.invoked_subcommand is None:
            pass

    @zardoz_var.command(name='set', help='Set variables for the server.')
    async def zardoz_var_set(ctx, var: str, val: int):
        DB.set_var(ctx.guild, var, val)
        await ctx.send(f'**{var}** = {val}')

    @zardoz_var.command(name='get', help='Print a variable value.')
    async def zardoz_var_get(ctx, var: str):
        val = DB.get_var(ctx.guild, var)
        if val is None:
            await ctx.send(f'**{var}** is not defined.')
        else:
            await ctx.send(f'**{var}** = {val}')

    @zardoz_var.command(name='del', help='Delete a variable.')
    async def zardoz_var_del(ctx, var: str):
        DB.del_var(ctx.guild, var)
        await ctx.send(f'**{var}** deleted')

    @zardoz_var.command(name='list', help='Print current variables.')
    async def zardoz_var_list(ctx):
        variables = DB.get_guild_vars(ctx.guild)
        if variables:
            result = [f'**{key}**: {val}' for key, val in variables.items()]
            await ctx.send('\n'.join(result))
        else:
            await ctx.send('**No variables set.**')

    #
    # Crit table subcommands
    #

    @bot.group(name='zcrit')
    async def zardoz_crit(ctx):
        pass

    @zardoz_crit.command(name='r')
    async def zardoz_crit_roll(ctx, table_name: str, val: typing.Optional[int]):
        try:
            table = CRITS[table_name]
        except KeyError:
            log.error(f'Error: no such crit: {table_name}.')
            return
        else:
            if val is None:
                val, name, effect = table.roll()
            else:
                name, effect = table.get(val)

            msg = f'**Result:** {table.die} ⤳ {val}\n'\
                  f'**Table:** {table.full_name} ({table.game}, {table.book})\n'\
                  f'**Name:** {name}\n'\
                  f'**Effect:** {effect}'
            await ctx.message.reply(msg)

    @bot.group(name='ztest')
    async def zardoz_test(ctx, arg):
        await ctx.send(f'parent: {arg}')

    @zardoz_test.command(name='subcmd')
    async def zardoz_test_subcmd(ctx, *extra_args):
        await ctx.send(f'subcmd: {extra_args}')


    bot.run(TOKEN)


if __name__ == '__main__':
    main()
