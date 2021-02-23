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
from .ztable import TableCommands
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
    bot.add_cog(TableCommands(bot, DB))
    bot.add_cog(VarCommands(bot, DB))
    bot.add_cog(ModeCommands(bot, DB))
    bot.add_cog(HistoryCommands(bot, DB))

    bot.run(TOKEN)


if __name__ == '__main__':
    main()
