import dice

import discord
from discord.ext import commands

import argparse
import json
import sys

from .logging import LoggingMixin
from .state import Database

from .zcrit import CritCommands
from .zhistory import HistoryCommands
from .zmode import ModeCommands
from .zroll import RollCommands
from .zvars import VarCommands


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--auth', default='auth.json')
    parser.add_argument('--database', default='db.json')
    args = parser.parse_args()

    log = LoggingMixin.get_logger()

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

    bot.add_cog(RollCommands(bot, DB))
    bot.add_cog(CritCommands(bot, DB))
    bot.add_cog(VarCommands(bot, DB))
    bot.add_cog(ModeCommands(bot, DB))
    bot.add_cog(HistoryCommands(bot, DB))

    bot.run(TOKEN)


if __name__ == '__main__':
    main()
