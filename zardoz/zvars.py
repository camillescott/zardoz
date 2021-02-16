from discord.ext import commands

from .logging import LoggingMixin


class VarCommands(commands.Cog, LoggingMixin):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

        super().__init__()

    @commands.group(name='zvar', help='Manage variables for the server.')
    async def zvar(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @zvar.command(name='list', help='Print current variables.')
    async def zvar_list(self, ctx):
        variables = self.db.get_guild_vars(ctx.guild)
        if variables:
            result = [f'**{key}**: {val}' for key, val in variables.items()]
            await ctx.send('\n'.join(result))
        else:
            await ctx.send('**No variables set.**')
    
    @zvar.command(name='set', help='Set variables for the server.')
    async def zvar_set(self, ctx, var: str, val: int):
        self.db.set_var(ctx.guild, var, val)
        await ctx.send(f'**{var}** = {val}')

    @zvar.command(name='get', help='Print a variable value.')
    async def zvar_get(self, ctx, var: str):
        val = self.db.get_var(ctx.guild, var)
        if val is None:
            await ctx.send(f'**{var}** is not defined.')
        else:
            await ctx.send(f'**{var}** = {val}')

    @zvar.command(name='del', help='Delete a variable.')
    async def zvar_del(self, ctx, var: str):
        self.db.del_var(ctx.guild, var)
        await ctx.send(f'**{var}** deleted')
