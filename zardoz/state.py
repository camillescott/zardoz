from enum import IntEnum, auto

from discord.ext import commands
from tinydb import TinyDB, Query, where


class GameMode(IntEnum):
    DEFAULT = auto()
    RT = auto()
    DND = auto()
    AW = auto()


MODE_META = {GameMode.DEFAULT: 'Default die is 1d6',
             GameMode.RT: 'Default die is 1d100; reports DoS/DoF',
             GameMode.DND: 'Default die is 1d20',
             GameMode.AW: 'Default die is 1d6'}


MODE_DICE = {GameMode.DEFAULT: '1d6',
             GameMode.RT: '1d100',
             GameMode.DND: '1d20',
             GameMode.AW: '1d6'}


class Database:

    def __init__(self, path):
        self.db = TinyDB(path)
        self.rolls = self.db.table('rolls')
        self.modes = self.db.table('modes')
        self.vars = self.db.table('vars')

    def add_guilds(self, guilds):
        for guild in guilds:
            if not self.modes.get(where('guild_id') == guild.id):
                self.modes.insert({'guild_id': guild.id,
                                   'mode': GameMode.DEFAULT})

    def add_roll(self, guild, member, expr, result):
        self.rolls.insert({'guild_id': guild.id,
                           'guild_name': guild.name,
                           'member_id': member.id,
                           'member_nick': member.nick,
                           'expr': expr,
                           'result': result})

    def query_guild_rolls(self, guild):
        RollsQ = Query()
        return self.rolls.search(RollsQ.guild_id == guild.id)

    def set_guild_mode(self, guild, mode):
        if not isinstance(mode, GameMode):
            try:
                mode = GameMode[mode]
            except KeyError:
                raise ValueError(f'{mode} is not a valid GameMode')
        
        self.modes.upsert({'guild_id': guild.id, 'mode': mode},
                          where('guild_id') == guild.id)

    def get_guild_mode(self, guild):
        result = self.modes.search(where('guild_id') == guild.id)
        if result:
            return GameMode(result[0]['mode'])
        else:
            self.set_guild_mode(guild, GameMode.DEFAULT)
            return GameMode.DEFAULT

    def set_var(self, guild, var, val):
        self.vars.upsert({'guild_id': guild.id,
                          'var': var,
                          'val': val},
                         (where('guild_id') == guild.id) & (where('var') == var))

    def get_var(self, guild, var):
        result =  self.vars.get((where('guild_id') == guild.id) & \
                                (where('var') == var))
        if result:
            return result['val']
        else:
            return None

    def get_guild_vars(self, guild):
        result = self.vars.search(where('guild_id') == guild.id)
        variables = {row['var']: row['val'] for row in result}
        return variables


class ModeConvert(commands.Converter):

    async def convert(self, ctx, argument):
        try:
            converted = GameMode[argument]
        except KeyError:
            raise commands.BadArgument(f'{argument} is not a valid mode.')
        return converted


class ModeCommand(commands.Converter):

    CMDS = ['set', 'get', 'list']

    async def convert(self, ctx, argument):
        if argument not in ModeCommand.CMDS:
            raise commands.BadArgument(f'Argument must be one of {ModeCommand.CMDS}.')
        async def mode_func(db, mode_arg = None):
            if argument == 'set':
                if mode_arg is None:
                    mode_arg = GameMode.DEFAULT
                db.set_guild_mode(ctx.guild, mode_arg)
                await ctx.send(f'**Set Mode:**: {GameMode(mode_arg).name}')
                return mode_arg
            if argument == 'get':
                current_mode = db.get_guild_mode(ctx.guild)
                await ctx.send(f'**Mode:**: {GameMode(current_mode).name}\n'\
                               f'*{MODE_META[current_mode]}*')
                return current_mode
            if argument == 'list':
                modes = '\n'.join((f'{mode.name}: {MODE_META[mode]}' for mode in GameMode))
                await ctx.send(modes)

        return mode_func


class VarCommand(commands.Converter):

    CMDS = ['set', 'get', 'list']

    async def convert(self, ctx, argument):
        if argument not in VarCommand.CMDS:
            raise commands.BadArgument(f'sub_cmd must be one of {VarCommand.CMDS}')

        async def var_func(db, var, val = 0):
            if var is None or argument == 'list':
                variables = db.get_guild_vars(ctx.guild)
                if variables:
                    result = [f'**{key}**: {val}' for key, val in variables.items()]
                    await ctx.send('\n'.join(result))
                else:
                    await ctx.send('**No variables set.**')
            if argument == 'set':
                db.set_var(ctx.guild, var, val)
                await ctx.send(f'**{var}** = {val}')
            if argument == 'get':
                val = db.get_var(ctx.guild, var)
                await ctx.send(f'**{var}** = {val}')

        return var_func
