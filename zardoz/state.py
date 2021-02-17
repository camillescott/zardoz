from datetime import datetime
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

    def add_roll(self, guild, member, roll, tag, result):
        self.rolls.insert({'time': datetime.now().timestamp(),
                           'guild_id': guild.id,
                           'member_id': member.id,
                           'member_nick': member.nick,
                           'member_name': member.name,
                           'roll': roll,
                           'tag': tag,
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

    def del_var(self, guild, var):
        self.vars.remove((where('guild_id') == guild.id) & (where('var') == var))

    def get_guild_vars(self, guild):
        result = self.vars.search(where('guild_id') == guild.id)
        variables = {row['var']: row['val'] for row in result}
        return variables

