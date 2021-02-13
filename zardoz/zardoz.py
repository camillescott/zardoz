import dice

import discord
from discord.ext import commands

import rich
from rich.logging import RichHandler

import json
import logging
import sys
import typing

from database import RollHistory
from rolls import resolve_expr


# Set up rich logging handler
# (discord.py uses the python logger)
FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger('discord')

with open('auth.json') as fp:
    auth = json.load(fp)

try:
    TOKEN = auth['token']
except:
    log.error('Must set "token" in auth.json!')
    sys.exit(1)
else:
    log.info(f'TOKEN: {TOKEN}')


HISTORY = RollHistory('rolls.json')

bot = commands.Bot(command_prefix='!')


@bot.command(name='zr', help='Evaluate a dice roll.')
async def zardoz_roll(ctx, *roll_expr):
    log.info(f'Received expr: "{roll_expr}" from {ctx.guild}:{ctx.author}')

    try:
        tokens, resolved = resolve_expr(*roll_expr)
    except Exception as e:
        log.error(f'Invalid expression: {roll_expr} {e}.')
        await ctx.send(f'You fucked up yer roll, {ctx.author}.')
    else:
        result = f'Request:    {" ".join(roll_expr)}\n'\
                 f'Rolled out: {resolved}'
        await ctx.send(result)
        HISTORY.add_roll(ctx.guild, ctx.author, ' '.join(roll_expr), resolved)


@bot.command(name='zhist', help='Display roll history.')
async def zardoz_history(ctx, max_elems: typing.Optional[int] = -1):
    log.info(f'CMD zhist {max_elems}.')

    guild_hist = HISTORY.query_guild(ctx.guild)
    guild_hist = '\n'.join((f'{item["member_nick"]}: {item["expr"]} => {item["result"]}' for item in guild_hist))
    await ctx.send(f'Roll History:\n{guild_hist}')

bot.run(TOKEN)
