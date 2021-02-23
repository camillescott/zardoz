#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2020
# File   : logging.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 22.02.2021

import logging

from rich.logging import RichHandler


def setup(log_file):
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s %(levelname)10s [%(filename)s:%(lineno)s - %(funcName)20s()] %(message)s',
        datefmt="[%x %X]"
    )

    logger = logging.getLogger()
    logger.addHandler(RichHandler())

    return logger


class LoggingMixin:

    def __init__(self, *args, **kwargs):
        self.log = self.get_logger()
        self.register_decos()
        
    def register_decos(self):

        try:
            @self.bot.before_invoke
            async def log_cmd_invoke(ctx):
                self.log.info(f'CMD: [{ctx.invoked_with} {ctx.message.content}] from {ctx.author}:{ctx.guild}')
        except AttributeError:
            pass

    @staticmethod
    def get_logger():
        return logging.getLogger()
