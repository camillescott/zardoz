import typing

from discord.ext import commands

from .database import fetch_guild_db
from .logging import LoggingMixin
from .state import GameMode, MODE_META


class ModeConvert(commands.Converter):

    async def convert(self, ctx, argument):
        try:
            converted = GameMode[argument]
        except KeyError:
            raise commands.BadArgument(f'{argument} is not a valid mode.')
        return converted


class ModeCommands(commands.Cog, LoggingMixin):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

        super().__init__()

    @commands.group(name='zmode', help='Manage game modes for the server')
    async def zmode(self, ctx):
        if ctx.invoked_subcommand is None:
            pass
    
    @zmode.command(name='set', help='Set the mode for the server.')
    @fetch_guild_db
    async def zmode_set(self, ctx, mode: typing.Optional[ModeConvert]):
        if mode is None:
            mode = GameMode.DEFAULT
        await ctx.guild_db.set_guild_mode(mode)
        await ctx.send(f'**Set Mode:** {GameMode(mode).name}')

    @zmode.command(name='get', help='Display the server mode.')
    @fetch_guild_db
    async def zardoz_mode_get(self, ctx):
        current_mode = await ctx.guild_db.get_guild_mode()
        await ctx.send(f'**Mode:**: {GameMode(current_mode).name}\n'\
                       f'*{MODE_META[current_mode]}*')

    @zmode.command(name='list', help='List available modes.')
    async def zardoz_mode_list(self, ctx):
        modes = '\n'.join((f'{mode.name}: {MODE_META[mode]}' for mode in GameMode))
        await ctx.send(modes)

