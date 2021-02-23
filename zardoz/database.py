#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2020
# File   : database.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 22.02.2021

import aiofiles
import aiosql
import aiosqlite

import asyncio
from datetime import datetime
import functools
import os
import sqlite3

from .logging import LoggingMixin
from .state import GameMode
from .utils import __pkg_dir__


def load_sql_commands(*args, **kwargs):
    mode = kwargs.get('mode', 'aiosqlite')
    cmd_file = os.path.join(__pkg_dir__, 'sql', 'commands.sql')
    cmds = aiosql.from_path(cmd_file, mode)
    return cmds


class DatabaseCache(LoggingMixin):

    def __init__(self, db_dir):
        self.cache = {}
        self.db_dir = db_dir
        db_dir.mkdir(parents=True, exist_ok=True)

        super().__init__()

        self.log.info(f'DatabaseCache using dir: {db_dir}')

    async def get_guild_db(self, guild_id: int):
        self.log.info(f'Fetch database for {guild_id}')
        db = self.cache.get(guild_id, None)
        if db is None:
            self.log.info(f'Database for {guild_id} not in cache.')
            db = await ZardozDatabase.build(self.db_dir, guild_id)
            self.cache[guild_id] = db
        return db

    async def close(self):
        self.log.info(f'Closing {len(self.cache)} database connections.')
        for guild_id, db in self.cache.items():
            await db.close()


class ZardozDatabase(LoggingMixin):

    def __init__(self, con, guild_id, async_mode=True):
        self.con = con
        self.con.row_factory = sqlite3.Row
        self.guild_id = guild_id

        if async_mode:
            self.cmds = load_sql_commands()
        else:
            self.cmds = load_sql_commands(mode='sqlite3')

        self._register_aiosql_commands(self.cmds)

        super().__init__()

    def _register_aiosql_commands(self, cmds):
        for cmd_name in cmds.available_queries:
            # get the method and bind the connection to it
            cmd_func = getattr(cmds, cmd_name)
            bound = functools.partial(cmd_func, self.con)

            # build the new method for ZardozDatabase
            @functools.wraps(bound)
            def wrapped_cmd(_self, *args, **kwargs):
                return bound(*args, **kwargs)

            # add it to ZardozDatabase instance
            new_name = f'{cmd_name}_cmd'
            setattr(self, new_name, bound)

    @classmethod
    async def build(cls, db_dir, guild_id):
        spec_file = os.path.join(__pkg_dir__, 'sql', 'database.sql')
        async with aiofiles.open(spec_file, mode='r') as fp:
            spec_script = await fp.read()

        path = db_dir.joinpath(f'{guild_id}.db')
        con = await aiosqlite.connect(path)
        await con.executescript(spec_script)
        await con.commit()

        return cls(con, guild_id)

    @staticmethod
    def convert_time(timestamp):
        return datetime.fromtimestamp(timestamp).astimezone()
        
    async def close(self):
        await self.con.close()

    async def add_roll(self, member_id: int, member_nick: str, 
                             member_name: str, roll: str, tag: str, 
                             result: str):
        await self.insert_roll_cmd(member_id=member_id, member_nick=member_nick,
                                   member_name=member_name, roll=roll,
                                   tag=tag, result=result,
                                   time=datetime.now().timestamp())
        await self.con.commit()

    async def get_rolls(self, member_id=None, max_rolls=5, since=None):
        async with self.get_rolls_cursor_cmd(max_rolls=max_rolls) as cur:
            async for row in cur:
                result = dict(row)
                result['time'] = self.convert_time(result['time'])
                yield result

    async def get_last_user_roll(self, member_id: int):
        roll = await self.get_last_user_roll_cmd(member_id)
        if not roll:
            return None

        roll = dict(roll)
        roll['time'] = self.convert_time(roll['time'])
        return roll

    async def get_merged_vars(self, member_id: int):
        user_vars = await self.get_user_vars(member_id)
        guild_vars = await self.get_guild_vars()
        guild_vars.update(user_vars)
        return guild_vars

    async def set_user_var(self, member_id: int, var: str, val: int):
        await self.set_user_var_cmd(member_id=member_id, var=var, val=val)
        await self.con.commit()

    async def get_user_var(self, member_id: int, var: str):
        result = await self.get_user_var_cmd(member_id=member_id, var=var)
        return result['val'] if result else None
    
    async def get_user_vars(self, member_id: int):
        user_vars = {}
        async with self.get_user_vars_cursor_cmd(member_id=member_id) as cur:
            async for row in cur:
                user_vars[row['var']] = row['val']
        return user_vars

    async def del_user_var(self, member_id: int, var: str):
        await self.del_user_var_cmd(member_id=member_id, var=var)
        await self.con.commit()

    async def set_guild_var(self, member_id: int, var: str, val: int):
        await self.set_guild_var_cmd(member_id=member_id, var=var, val=val)
        await self.con.commit()

    async def get_guild_var(self, var: str):
        result = await self.get_guild_var_cmd(var=var)
        return result['val'] if result else None
    
    async def get_guild_vars(self):
        guild_vars = {}
        async with self.get_guild_vars_cursor_cmd() as cur:
            async for row in cur:
                guild_vars[row['var']] = row['val']
        return guild_vars

    async def del_guild_var(self, var: str):
        await self.del_guild_var_cmd(var=var)
        await self.con.commit()
    
    async def set_guild_mode(self, mode: GameMode):
        if not isinstance(mode, GameMode):
            try:
                mode = GameMode[mode]
            except KeyError:
                raise ValueError(f'{mode} is not a valid GameMode')
        await self.set_guild_var(0, 'MODE', mode)

    async def get_guild_mode(self):
        mode = await self.get_guild_var('MODE')
        if mode:
            return GameMode(mode)
        else:
            await self.set_guild_mode(GameMode.DEFAULT)
            return GameMode.DEFAULT


def fetch_guild_db(func):

    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        ctx.guild_db = await self.db.get_guild_db(ctx.guild.id)
        ctx.game_mode = await ctx.guild_db.get_guild_mode()
        ctx.variables = await ctx.guild_db.get_merged_vars(ctx.author.id)
        return await func(self, ctx, *args, **kwargs)

    return wrapper
