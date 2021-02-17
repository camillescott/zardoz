from datetime import datetime
import os
from pathlib import Path

from xdg import xdg_data_home


__pkg_dir__ = os.path.abspath(os.path.dirname(__file__))
__time_format__ = '%a %b %d %I:%M%p %Z'


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

