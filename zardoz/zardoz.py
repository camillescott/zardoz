import dice

import discord
from discord.ext import commands
from xdg import xdg_data_home

import argparse
import json
from pathlib import Path
import sys

from .logging import setup as setup_logger
from .state import Database

from .zcrit import CritCommands
from .zhistory import HistoryCommands
from .zmode import ModeCommands
from .zroll import RollCommands
from .zvars import VarCommands


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--auth', default='auth.json')

    parser.add_argument(
        '--database',
        type=lambda p: Path(p).absolute(),
        default=xdg_data_home().joinpath('zardoz-bot', 'db.json')
    )
    parser.add_argument(
        '--log-file',
        type=lambda p: Path(p).absolute(),
        default=xdg_data_home().joinpath('zardoz-bot', 'bot.log')
    )
    args = parser.parse_args()

    log = setup_logger(log_file=args.log_file)

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
    args.database.parent.mkdir(exist_ok=True)
    DB = Database(args.database)


    bot = commands.Bot(command_prefix='/')

    @bot.event
    async def on_ready():
        log.info(f'Ready: member of {bot.guilds}')
        log.info(f'Users: {bot.users}')
        DB.add_guilds(bot.guilds)

    bot.add_cog(RollCommands(bot, DB))
    bot.add_cog(CritCommands(bot, DB))
    bot.add_cog(VarCommands(bot, DB))
    bot.add_cog(ModeCommands(bot, DB))
    bot.add_cog(HistoryCommands(bot, DB))

    bot.run(TOKEN)


if __name__ == '__main__':
    main()
