#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# zardoz/zardoz.py
# Copyright (c) 2021 Camille Scott <camille.scott.w@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import json
import logging
import os
from pathlib import Path
import sys
import textwrap

from discord.ext import commands

from . import __version__, __splash__, __about__, __testing__
from .utils import default_log_file, default_database_dir


class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass


class Bot(commands.Bot):

    async def close(self):
        log = logging.getLogger()
        log.info('DatabaseCache close()')
        await self.DB.close()
        log.info('Bot close()')
        await super().close()
        log.info('Bot closed.')


def add_parser_args(parser, token_name='ZARDOZ_TOKEN'):
    parser.add_argument(
        '--secret-token',
        help=f'The secret token for the bot, '\
             f'from the discord developer portal. '\
             f'If you have set ${token_name}, this '\
             f'option will override that.'
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


def main():
    parser = argparse.ArgumentParser(
        description=f'{__splash__}\n{__about__}',
        formatter_class=CustomFormatter
    )
    subparsers = parser.add_subparsers()

    bot = subparsers.add_parser('bot')
    add_parser_args(bot)
    bot.set_defaults(func=run_bot)

    args = parser.parse_args()
    args.func(args)


def run_bot(args):

    bot, db = build_bot(args)

    @bot.event
    async def on_ready():
        log = logging.getLogger()
        log.info(f'Ready: member of {bot.guilds}')
        log.info(f'Users: {bot.users}')

    @bot.command(name='zabout', help='Project info.')
    async def zabout(ctx):
        msg = f'version: {__version__}\n'\
              f'source: https://github.com/camillescott/zardoz/releases/tag/v{__version__}\n'\
              f'active installs: {len(bot.guilds)}'
        await ctx.message.reply(msg)

    bot.run(args.secret_token)


def build_bot(args, token_name='ZARDOZ_TOKEN', prefix='z', loop=None):

    from .database import DatabaseCache
    from .logging import setup as setup_logger
    
    from .cogs.history import HistoryCommands
    from .cogs.mode import ModeCommands
    from .cogs.roll import RollCommands
    from .cogs.sample import SampleCommands
    from .cogs.vars import VarCommands

    log = setup_logger(args.log)

    TOKEN = args.secret_token
    if not TOKEN:
        try:
            TOKEN = os.environ[token_name]
        except KeyError:
            log.error(f'Must set ${token_name} or use --secret-token')
            sys.exit(1)
        else:
            log.info(f'Got secret token from ${token_name}.')
    args.secret_token = TOKEN

    # get a handle for the history database
    DB = DatabaseCache(args.database_dir)

    prefix = f'/{prefix}' if not __testing__ else f'!{prefix}'
    log.info(f'Prefix is: {prefix}')
    bot = Bot(command_prefix=prefix, loop=loop)
    bot.DB = DB

    bot.add_cog(RollCommands(bot, DB))
    bot.add_cog(VarCommands(bot, DB))
    bot.add_cog(ModeCommands(bot, DB))
    bot.add_cog(HistoryCommands(bot, DB))
    bot.add_cog(SampleCommands(bot, DB))

    return bot, DB


if __name__ == '__main__':
    main()
