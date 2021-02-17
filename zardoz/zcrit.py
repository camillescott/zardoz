import glob
import os
import typing

import dice
import yaml

from discord.ext import commands

from .logging import LoggingMixin
from .utils import __pkg_dir__


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


def load_crit_tables(log=None):
    
    files = glob.glob(os.path.join(__pkg_dir__, 'crits', '*.yaml'))
    tables = {}
    for file_path in files:
        table = CritTable(file_path)
        tables[table.slug] = table
    return tables


TABLES = load_crit_tables()


class TableConvert(commands.Converter):

    async def convert(self, ctx, argument):
        try:
            table = TABLES[argument]
        except KeyError:
            raise commands.BadArgument(f'{argument} is not a valid table.')
        return table


class CritCommands(commands.Cog, LoggingMixin):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        super().__init__()

        self.log.info(f'Loaded crits: {TABLES}')

    @commands.group(name='zcrit', help='Roll on a crit table.')
    async def zcrit(self, ctx, table: typing.Optional[TableConvert],
                               val: typing.Optional[int]):
        if ctx.invoked_subcommand is not None:
            return

        if table is None:
            await ctx.invoke(self.zcrit_list)
            return

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

    @zcrit.command(name='list', help='List available crit tables.')
    async def zcrit_list(self, ctx):
        header = '**Available Tables:**'
        body = []
        for slug, table in TABLES.items():
            body.append(f'`{slug:15}` {table.full_name} ({table.game}, {table.book})')
        body = '\n'.join(body)
        await ctx.message.reply(f'{header}\n{body}')
