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
import os
from pathlib import Path
import sys
import textwrap

from discord.ext import commands

from . import __version__, __splash__, __about__, __testing__
from .rt.simulate import zimulate
from .utils import default_log_file, default_database_dir, EnumAction



class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter,
                      argparse.RawDescriptionHelpFormatter):
    pass


def main():

    from .rt.combat import COMBAT_ACTIONS
    from .rt.items import ItemAvailability
    from .rt.weapons import (WeaponClass, WeaponType, DamageType,
                             Craftsmanship)

    parser = argparse.ArgumentParser(
        description=f'{__splash__}\n{__about__}',
        formatter_class=CustomFormatter
    )
    subparsers = parser.add_subparsers()

    bot = subparsers.add_parser('bot')
    bot.add_argument(
        '--secret-token',
        help='The secret token for the bot, '\
             'from the discord developer portal. '\
             'If you have set $ZARDOZ_TOKEN, this '\
             'option will override that.'
    )
    bot.add_argument(
        '--database-dir',
        type=lambda p: Path(p).absolute(),
        default=default_database_dir(debug=__testing__),
        help='Directory for the bot databases. Default follows the '\
             'XDG specifiction.'
    )
    bot.add_argument(
        '--log',
        type=lambda p: Path(p).absolute(),
        default=default_log_file(debug=__testing__),
        help='Path to the log file. Default follows the '\
             'XDG specifiction.'
    )
    bot.set_defaults(func=dize)

    simulate = subparsers.add_parser('zimulate')
    simulate.add_argument(
        '-BS',
        '--ballistic-skill',
        default=40,
        type=int
    )
    simulate.add_argument(
        '--actions',
        nargs='+',
        choices=COMBAT_ACTIONS.keys()
    )
    simulate.add_argument(
        '--target-range',
        default=10,
        type=int
    )
    simulate.add_argument(
        '--name',
        default='RT Weapon',
    )
    simulate.add_argument(
        '--availability',
        default=ItemAvailability.Scarce,
        action=EnumAction,
        type=ItemAvailability
    )
    simulate.add_argument(
        '--weapon-class',
        default=WeaponClass.Pistol,
        action=EnumAction,
        type=WeaponClass
    )
    simulate.add_argument(
        '--type',
        default=WeaponType.Las,
        type=WeaponType,
        action=EnumAction
    )
    simulate.add_argument(
        '--range',
        default=20,
        type=int
    )
    simulate.add_argument(
        '--rof-single',
        default=True,
        type=bool
    )
    simulate.add_argument(
        '--rof-semi',
        default=0,
        type=int
    )
    simulate.add_argument(
        '--rof-auto',
        default=0,
        type=int
    )
    simulate.add_argument(
        '--damage-d10',
        default=1,
        type=int
    )
    simulate.add_argument(
        '--damage-bonus',
        default=3,
        type=int
    )
    simulate.add_argument(
        '--damage-type',
        default=DamageType.Energy,
        type=DamageType,
        action=EnumAction
    )
    simulate.add_argument(
        '--pen',
        default=0,
        type=int
    )
    simulate.add_argument(
        '--clip',
        default=10,
        type=int
    )
    simulate.add_argument(
        '--reload-time',
        default=1.0,
        type=float
    )
    simulate.add_argument(
        '--mass',
        default=2.0,
        type=float
    )
    simulate.add_argument(
        '--craftsmanship',
        default=Craftsmanship.Common,
        type=Craftsmanship,
        action=EnumAction
    )
    simulate.add_argument(
        '--n-trials',
        '-N',
        default=10000,
        type=int
    )
    simulate.add_argument(
        '--plot',
        default='text',
        choices = ['text', 'image']
    )
    simulate.set_defaults(func=zimulate)

    args = parser.parse_args()
    args.func(args)


def dize(args):

    from .database import DatabaseCache
    from .logging import setup as setup_logger
    
    from .ztable import TableCommands
    from .zhistory import HistoryCommands
    from .zmode import ModeCommands
    from .zroll import RollCommands
    from .zvars import VarCommands

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

    prefix = '/' if not __testing__ else '!'
    bot = ZardozBot(command_prefix=prefix)

    @bot.event
    async def on_ready():
        log.info(f'Ready: member of {bot.guilds}')
        log.info(f'Users: {bot.users}')

    @bot.command(name='zabout', help='Project info.')
    async def zabout(ctx):
        msg = f'version: {__version__}\n'\
              f'source: https://github.com/camillescott/zardoz/releases/tag/v{__version__}\n'\
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
