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

from .state import Database, GameMode, ModeCommand, ModeConvert, MODE_META
from .rolls import resolve_expr, solve_expr


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
        log.info(f'Received expr: "{args}" from {ctx.guild}:{ctx.author}')

        roll_expr, tag = [], ''
        for i, token in enumerate(args):
            if token.startswith('#'):
                roll_expr = args[:i]
                tag = ' '.join(args[i:])
        if not tag:
            roll_expr = args
        tag = tag.strip('# ')

        game_mode = DB.get_guild_mode(ctx.guild)

        try:
            tokens, resolved = resolve_expr(*roll_expr, mode=game_mode)
            solved = list(solve_expr(tokens))
        except ValueError  as e:
            log.error(f'Invalid expression: {roll_expr} {e}.')
            await ctx.send(f'You fucked up yer roll, {ctx.author}.')
        else:
            user = ctx.author
            result = [f'**{user.nick if user.nick else user.name}**' + (f', *{tag}*' if tag else ''),
                      f'Request: `{" ".join(roll_expr)}`',
                      f'Rolled out: `{resolved}`',
                      f'Result: `{solved}`']
            await ctx.send('\n'.join(result))
            DB.add_roll(ctx.guild, ctx.author, ' '.join(roll_expr), resolved)


    @bot.command(name='zhist', help='Display roll history.')
    async def zardoz_history(ctx, max_elems: typing.Optional[int] = -1):
        log.info(f'CMD zhist {max_elems}.')

        guild_hist = DB.query_guild(ctx.guild)
        guild_hist = '\n'.join((f'{item["member_nick"]}: {item["expr"]} => {item["result"]}' for item in guild_hist))
        await ctx.send(f'Roll History:\n{guild_hist}')


    @bot.command(name='zmode')
    async def zardoz_mode(ctx, sub_cmd: ModeCommand, 
                          mode: typing.Optional[ModeConvert]):
        current_mode = sub_cmd(DB, mode)
        await ctx.send(f'**Mode:**: {GameMode(current_mode).name}\n'\
                       f'*{MODE_META[current_mode]}*')

    bot.run(TOKEN)


if __name__ == '__main__':
    main()
