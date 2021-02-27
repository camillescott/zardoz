#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2020
# File   : utils.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 22.02.2021

import argparse
from dataclasses import is_dataclass
from enum import Enum
from typing import TypeVar, Type, Callable, List, Dict, Any
from datetime import datetime
import functools
import os
from pathlib import Path
import random

import discord
from xdg import xdg_data_home


__pkg_dir__ = os.path.abspath(os.path.dirname(__file__))
__time_format__ = '%a %b %d %I:%M%p %Z'

_T = TypeVar("_T")
_Self = TypeVar("_Self")
_VarArgs = List[Any]
_KWArgs = Dict[str, Any]


FAILURE = 'F 🛇'
SUCCESS = 'S ✅'


def d10():
    return random.randint(1, 10)


def d100():
    return random.randint(1, 100)


def Nd10(n=1):
    return [random.randint(1,10) for _ in range(n)]


def Nd100(n=1):
    return [random.randint(1,100)  for _ in range(n)]


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


def reverse_number(num: int):
    result = 0
    while (num > 0):
        result = (num * 10) + (num % 10)
        num = num // 10
    return result


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


class EnumAction(argparse.Action):
    """
    Argparse action for handling Enums
    """
    def __init__(self, **kwargs):
        # Pop off the type value
        enum = kwargs.pop("type", None)

        # Ensure an Enum subclass is provided
        if enum is None:
            raise ValueError("type must be assigned an Enum when using EnumAction")
        if not issubclass(enum, Enum):
            raise TypeError("type must be an Enum when using EnumAction")

        # Generate choices from the Enum
        kwargs.setdefault("choices", tuple(e.name for e in enum))

        super(EnumAction, self).__init__(**kwargs)

        self._enum = enum

    def __call__(self, parser, namespace, values, option_string=None):
        # Convert value back into an Enum
        enum = self._enum[values]
        setattr(namespace, self.dest, enum)


#
# Dataclass utilities taken from: https://gist.github.com/mikeholler/4be180627d3f8fceb55704b729464adb
#

def _kwarg_only_init_wrapper(
        self: _Self,
        init: Callable[..., None],
        *args: _VarArgs,
        **kwargs: _KWArgs
) -> None:
    if len(args) > 0:
        raise TypeError(
            f"{type(self).__name__}.__init__(self, ...) only allows keyword arguments. Found the "
            f"following positional arguments: {args}"
        )
    init(self, **kwargs)


def _positional_arg_only_init_wrapper(
        self: _Self,
        init: Callable[..., None],
        *args: _VarArgs,
        **kwargs: _KWArgs
) -> None:
    if len(kwargs) > 0:
        raise TypeError(
            f"{type(self).__name__}.__init__(self, ...) only allows positional arguments. Found "
            f"the following keyword arguments: {kwargs}"
        )
    init(self, *args)


def require_kwargs(cls: Type[_T]) -> Type[_T]:
    """
    Force a dataclass's init function to only work if called with keyword arguments.
    If parameters are not positional-only, a TypeError is thrown with a helpful message.
    This function may only be used on dataclasses.
    This works by wrapping the __init__ function and dynamically replacing it. Therefore,
    stacktraces for calls to the new __init__ might look a bit strange. Fear not though,
    all is well.
    Note: although this may be used as a decorator, this is not advised as IDEs will no longer
    suggest parameters in the constructor. Instead, this is the recommended usage::
        from dataclasses import dataclass
        @dataclass
        class Foo:
            bar: str
        require_kwargs_on_init(Foo)
    """

    if cls is None:
        raise TypeError("Cannot call with cls=None")
    if not is_dataclass(cls):
        raise TypeError(
            f"This decorator only works on dataclasses. {cls.__name__} is not a dataclass."
        )

    original_init = cls.__init__

    def new_init(self: _Self, *args: _VarArgs, **kwargs: _KWArgs) -> None:
        _kwarg_only_init_wrapper(self, original_init, *args, **kwargs)

    # noinspection PyTypeHints
    cls.__init__ = new_init  # type: ignore

    return cls


def require_positional_args(cls: Type[_T]) -> Type[_T]:
    """
    Force a dataclass's init function to only work if called with positional arguments.
    If parameters are not positional-only, a TypeError is thrown with a helpful message.
    This function may only be used on dataclasses.
    This works by wrapping the __init__ function and dynamically replacing it. Therefore,
    stacktraces for calls to the new __init__ might look a bit strange. Fear not though,
    all is well.
    Note: although this may be used as a decorator, this is not advised as IDEs will no longer
    suggest parameters in the constructor. Instead, this is the recommended usage::
        from dataclasses import dataclass
        @dataclass
        class Foo:
            bar: str
        require_positional_args_on_init(Foo)
    """

    if cls is None:
        raise TypeError("Cannot call with cls=None")
    if not is_dataclass(cls):
        raise TypeError(
            f"This decorator only works on dataclasses. {cls.__name__} is not a dataclass."
        )

    original_init = cls.__init__

    def new_init(self: _Self, *args: _VarArgs, **kwargs: _KWArgs) -> None:
        _positional_arg_only_init_wrapper(self, original_init, *args, **kwargs)

    # noinspection PyTypeHints
    cls.__init__ = new_init  # type: ignore

    return cls
