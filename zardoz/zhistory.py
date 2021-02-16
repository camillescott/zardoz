import typing

from discord.ext import commands

from .logging import LoggingMixin


class HistoryCommands(commands.Cog, LoggingMixin):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db 

        super().__init__()

    @commands.command(name='zhist', help='Display roll history.')
    async def zhist(self, ctx, max_elems: typing.Optional[int] = -1):

        guild_hist = self.db.query_guild_rolls(ctx.guild)
        if max_elems > 0:
            guild_hist = guild_hist[-max_elems:]

        records = []
        for row in guild_hist:
            name = row.get('member_nick', None)
            if name is None:
                name = row.get('member_name', row.get('member_nick', 'Unknown'))
            records.append(f'{name}: {row["expr"]} ⟿  {row["result"]}')

        guild_hist = '\n'.join(records)
        await ctx.send(f'Roll History:\n{guild_hist}')


