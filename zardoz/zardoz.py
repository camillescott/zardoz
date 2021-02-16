import dice

import discord
from discord.ext import commands
from xdg import xdg_data_home

import argparse
import json
import os
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
    parser.add_argument(
        '--secret-token',
        help='The secret token for the bot, '\
             'from the discord developer portal. '\
             'If you have set ZARDOZ_TOKEN, this '\
             'option will override that.'
    )
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

    TOKEN = args.secret_token
    if not TOKEN:
        try:
            TOKEN = os.environ['ZARDOZ_TOKEN']
        except KeyError:
            log.error('Must set ZARDOZ_TOKEN or use --secret-token')
            sys.exit(1)
        else:
            log.info('Got secret token from $ZARDOZ_TOKEN.')

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
