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

from .state import Database, GameMode, ModeConvert, MODE_META, VarCommand
from .rolls import resolve_expr, solve_expr, RollList, DiceDelta, handle_roll


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
        DB.add_guilds(bot.guilds)

    @bot.command(name='z', help='Evaluate a dice roll.')
    async def zardoz_roll(ctx, *args):

        game_mode = DB.get_guild_mode(ctx.guild)
        tag, roll_expr, resolved, solved = await handle_roll(ctx, log, DB, game_mode, *args)
        if not solved:
            return

        user = ctx.author

        if isinstance(solved, DiceDelta):
            roll_desc = solved.describe(mode = game_mode)
        else:
            roll_desc = list(solved)

        header = f'{user.mention}' + (f', *{tag}*' if tag else '')
        result = [f'*Request:*\n```{" ".join(roll_expr)}```',
                  f'*Rolled out:*\n```{resolved}```',
                  f'*Result:*\n```{roll_desc}```']
        result = ''.join(result)
        msg = '\n'.join((header, result))

        await ctx.send(msg)

    @bot.command(name='zq', help='Evaluate a dice roll, quietly.')
    async def zardoz_quiet_roll(ctx, *args):

        game_mode = DB.get_guild_mode(ctx.guild)
        tag, roll_expr, resolved, solved = await handle_roll(ctx, log, DB, game_mode, *args)
        if not solved:
            return

        user = ctx.author

        if isinstance(solved, DiceDelta):
            roll_desc = solved.describe(mode = game_mode)
        else:
            roll_desc = list(solved)

        header = f'**{user.mention}**' + (f', *{tag}*' if tag else '')
        result =f'```{roll_desc}```'
        msg = f'{header}\n{result}'

        await ctx.send(msg)

    @bot.command(name='zs', help='Make a secret roll and DM to member.')
    async def zardoz_secret_roll(ctx, member: discord.Member, *args):

        game_mode = DB.get_guild_mode(ctx.guild)
        tag, roll_expr, resolved, solved = await handle_roll(ctx, log, DB, game_mode, *args)
        if not solved:
            return

        user = ctx.author

        if isinstance(solved, DiceDelta):
            roll_desc = solved.describe(mode = game_mode)
        else:
            roll_desc = list(solved)

        header = f'from **{user}**: ' + (f'*{tag}*' if tag else '')
        result = [f'*Request:*\n```{" ".join(roll_expr)}```',
                  f'*Rolled out:*\n```{resolved}```',
                  f'*Result:*\n```{roll_desc}```']
        result = ''.join(result)
        msg = '\n'.join((header, result))

        await member.send(msg)

    @bot.command(name='zhist', help='Display roll history.')
    async def zardoz_history(ctx, max_elems: typing.Optional[int] = -1):
        log.info(f'CMD zhist {max_elems}.')

        guild_hist = DB.query_guild_rolls(ctx.guild)
        if max_elems > 0:
            guild_hist = guild_hist[-max_elems:]
        guild_hist = '\n'.join((f'{item["member_nick"]}: {item["expr"]} ⟿  {item["result"]}' for item in guild_hist))
        await ctx.send(f'Roll History:\n{guild_hist}')

    #
    # Mode subcommands
    #

    @bot.group(name='zmode', help='Set the game mode for the server')
    async def zardoz_mode(ctx):
        if ctx.invoked_subcommand is None:
            pass
    
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

    @bot.command(name='zvar', help='Set a variable for the server')
    async def zardoz_var(ctx, sub_cmd: VarCommand,
                              var: typing.Optional[str],
                              val: typing.Optional[int] = 0):
        await sub_cmd(DB, var, val = val)


    bot.run(TOKEN)


if __name__ == '__main__':
    main()
