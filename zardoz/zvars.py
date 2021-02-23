#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2020
# File   : zvars.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 22.02.2021

from discord.ext import commands

from .database import fetch_guild_db
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
    @fetch_guild_db
    async def zvar_list(self, ctx):
        variables = await ctx.guild_db.get_guild_vars()
        if variables:
            result = [f'**{key}**: {val}' for key, val in variables.items()]
            await ctx.send('\n'.join(result))
        else:
            await ctx.send('**No variables set.**')
    
    @zvar.command(name='set', help='Set variables for the server.')
    @fetch_guild_db
    async def zvar_set(self, ctx, var: str, val: int):
        await ctx.guild_db.set_guild_var(ctx.author.id, var, val)
        await ctx.send(f'**{var}** = {val}')

    @zvar.command(name='get', help='Print a variable value.')
    @fetch_guild_db
    async def zvar_get(self, ctx, var: str):
        val = await ctx.guild_db.get_guild_var(var)
        if val is None:
            await ctx.send(f'**{var}** is not defined.')
        else:
            await ctx.send(f'**{var}** = {val}')

    @zvar.command(name='del', help='Delete a variable.')
    @fetch_guild_db
    async def zvar_del(self, ctx, var: str):
        await ctx.guild_db.del_guild_var(var)
        await ctx.send(f'**{var}** deleted')
