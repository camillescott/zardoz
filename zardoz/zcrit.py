import glob
import os
import typing

import dice
import yaml

from discord.ext import commands

from .logging import LoggingMixin
from .utils import __pkg_dir__

class CritCommands(commands.Cog, LoggingMixin):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        super().__init__()

        self.tables = load_crit_tables(self.log)
        self.log.info(f'Loaded crits: {self.tables}')

    @commands.group(name='zcrit', help='Roll on a crit table.')
    async def zcrit(self, ctx):
        pass

    @zcrit.command(name='r')
    async def zcrit_roll(self, ctx, table_name: str, val: typing.Optional[int]):
        try:
            table = self.tables[table_name]
        except KeyError:
            self.log.error(f'Error: no such crit: {table_name}.')
            await ctx.message.reply(f'No crit table named {table_name}.')
        else:
            try:
                if val is None:
                    val, name, effect = table.roll()
                else:
                    name, effect = table.get(val)
            except ValueError:
                await ctx.message.reply(f'Bad crit table value. Perils be upon ye.')
            else:
                msg = f'**Result:** {table.die} ⤳ {val}\n'\
                      f'**Table:** {table.full_name} ({table.game}, {table.book})\n'\
                      f'**Name:** {name}\n'\
                      f'**Effect:** {effect}'
                await ctx.message.reply(msg)


def load_crit_tables(log=None):
    
    files = glob.glob(os.path.join(__pkg_dir__, 'crits', '*.yaml'))
    tables = {}
    for file_path in files:
        table = CritTable(file_path)
        tables[table.slug] = table
    return tables


class CritTable:

    def __init__(self, table_yaml):
        with open(table_yaml) as fp:
            data = yaml.safe_load(fp)

        self.full_name = data['full_name']
        self.slug = data['slug']
        self.game = data['game']
        self.book = data['book']
        self.die = data['die']
        self.rolls = data['rolls']
    
    
    def get(self, roll):
        for option in self.rolls:
            lower, upper = option['range']
            name = '' if not option['name'] else option['name'].strip()
            if lower <= roll <= upper:
                return name, ' '.join(option['effect'].split())

        raise ValueError(f'No entry for {roll}')

    def roll(self, modifers = None):
        rolled_val = int(dice.roll(self.die))
        name, effect = self.get(rolled_val)

        return rolled_val, name, effect


