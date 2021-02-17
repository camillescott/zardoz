import dice

import discord
from discord.ext import commands

import argparse
import json
import os
from pathlib import Path
import sys
import textwrap

from .logging import setup as setup_logger

from . import __version__, __splash__, __about__, __testing__
from .database import DatabaseCache
from .utils import default_log_file, default_database_dir
from .zcrit import CritCommands
from .zhistory import HistoryCommands
from .zmode import ModeCommands
from .zroll import RollCommands
from .zvars import VarCommands


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass


def main():

    parser = argparse.ArgumentParser(
        description=f'{__splash__}\n{__about__}',
        formatter_class=CustomFormatter
    )
    parser.add_argument(
        '--secret-token',
        help='The secret token for the bot, '\
             'from the discord developer portal. '\
             'If you have set $ZARDOZ_TOKEN, this '\
             'option will override that.'
    )
    parser.add_argument(
        '--database-dir',
        type=lambda p: Path(p).absolute(),
        default=default_database_dir(debug=__testing__),
        help='Directory for the bot databases. Default follows the '\
             'XDG specifiction.'
    )
    parser.add_argument(
        '--log',
        type=lambda p: Path(p).absolute(),
        default=default_log_file(debug=__testing__),
        help='Path to the log file. Default follows the '\
             'XDG specifiction.'
    )
    args = parser.parse_args()

    log = setup_logger(args.log)

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
    DB = DatabaseCache(args.database_dir)

    class ZardozBot(commands.Bot):

        async def close(self):
            log.info('DatabaseCache close()')
            await DB.close()
            log.info('Bot close()')
            await super().close()
            log.info('Bot closed.')

    bot = ZardozBot(command_prefix='/')

    @bot.event
    async def on_ready():
        log.info(f'Ready: member of {bot.guilds}')
        log.info(f'Users: {bot.users}')

    @bot.command(name='zabout', help='Project info.')
    async def zabout(ctx):
        msg = f'version: {__version__}\n'\
              f'source: https://github.com/camillescott/zardoz\n'\
              f'active installs: {len(bot.guilds)}'
        await ctx.message.reply(msg)

    bot.add_cog(RollCommands(bot, DB))
    bot.add_cog(CritCommands(bot, DB))
    bot.add_cog(VarCommands(bot, DB))
    bot.add_cog(ModeCommands(bot, DB))
    bot.add_cog(HistoryCommands(bot, DB))

    bot.run(TOKEN)


if __name__ == '__main__':
    main()
