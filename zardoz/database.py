import aiofiles
import aiosql
import aiosqlite

import asyncio
import sqlite3

from .utils import __pkg_dir__


def load_sql_commands(*args, **kwargs):
    cmd_file = os.path.join(__pkg_dir__, 'sql', 'commands.sql')
    cmds = aiosql.from_path(cmd_file, "aiosqlite")
    return cmds


class ZardozDatabase:

    def __init__(self, con, guild_id):
        self.con = con
        self.guild_id = guild_id
        self.cmds = load_sql_commands()
        # make commands methods dynamically


    @classmethod
    async def build(cls, db_dir, guild_id):
        spec_file = os.path.join(__pkg_dir__, 'sql', 'database.sql')
        async with aiofiles.open(spec_file, mode='r') as fp:
            spec_script = await fp.read()

        path = db_dir.joinpath(f'{guild_id}.db')
        con = await aiosqlite.connect(path)

        return cls(con, guild_id)
        
