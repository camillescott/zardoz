#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2020
# File   : zvars.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 22.02.2021

from discord.ext import commands

from ..database import fetch_guild_db
from ..logging import LoggingMixin


class VarCommands(commands.Cog, LoggingMixin):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

        super().__init__()

    @commands.group(name='var')
    async def var(self, ctx):
        '''
        Manage variables for the server.
        '''
        if ctx.invoked_subcommand is None:
            pass

    @var.command(name='list')
    @fetch_guild_db
    async def var_list(self, ctx):
        '''
        List currently set variables and values.
        '''
        variables = await ctx.guild_db.get_guild_vars()
        if variables:
            result = [f'**{key}**: {val}' for key, val in variables.items()]
            await ctx.send('\n'.join(result))
        else:
            await ctx.send('**No variables set.**')
    
    @var.command(name='set')
    @fetch_guild_db
    async def var_set(self, ctx, var: str, val: int):
        '''
        Set a variable.
        '''
        await ctx.guild_db.set_guild_var(ctx.author.id, var, val)
        await ctx.send(f'**{var}** = {val}')

    @var.command(name='get')
    @fetch_guild_db
    async def var_get(self, ctx, var: str):
        '''
        Get the given variable's value.
        '''
        val = await ctx.guild_db.get_guild_var(var)
        if val is None:
            await ctx.send(f'**{var}** is not defined.')
        else:
            await ctx.send(f'**{var}** = {val}')

    @var.command(name='del')
    @fetch_guild_db
    async def var_del(self, ctx, var: str):
        '''
        Delete the given variable.
        '''
        await ctx.guild_db.del_guild_var(var)
        await ctx.send(f'**{var}** deleted')
