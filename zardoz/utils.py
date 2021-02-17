from datetime import datetime
import functools
import os
from pathlib import Path

import discord
from xdg import xdg_data_home


__pkg_dir__ = os.path.abspath(os.path.dirname(__file__))
__time_format__ = '%a %b %d %I:%M%p %Z'

FAILURE = 'F 🛇'
SUCCESS = 'S ✅'


def default_database_dir(debug=False):
    if not debug:
        return xdg_data_home().joinpath('zardoz-bot', 'databases')
    else:
        return xdg_data_home().joinpath('zardoz-bot', 'debug', 'databases')


def default_log_file(debug=False):
    if not debug:
        return xdg_data_home().joinpath('zardoz-bot', 'bot.log')
    else:
        return xdg_data_home().joinpath('zardoz-bot', 'debug', 'bot.log')


def handle_http_exception(func):

    @functools.wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        try:
            return await func(self, ctx, *args, **kwargs)
        except discord.HTTPException:
            await ctx.message.reply('Hey broh, that\'s a big response.'\
                                    ' Try dialing back your request,'\
                                    ' I\'m only human.')
            raise
    return wrapper
