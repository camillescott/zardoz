#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : rolls.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 22.02.2021

from dice import DiceBaseException
from discord.ext import commands

import logging
import re

from .database import ZardozDatabase
from .state import GameMode, MODE_DICE, MAX_DICE_PER_ROLL
from .utils import SUCCESS, FAILURE
from .dice import roll as roll_expr
from .dice.elements import Comparison, Dice
from .dice.exceptions import DiceBaseException
from .dice.utilities import single


log = logging.getLogger()

OPS = ['+', '-', '<=', '<', '>=', '>', '(', ')', '==', '.+', '.-', '|', r'#']
DELIMS = [r'\s']
SPLIT_PAT = '|'.join(list(map(re.escape, OPS)) + DELIMS)


def split_tokens(word):
    log.info(f'SPLIT "{word}" on: "{SPLIT_PAT}"')
    return [t for t in re.split(f'({SPLIT_PAT})', word)]


def filter_tokens(tokens):
    return [t for t in tokens if t and not re.match(r'\s', t)]


def tokenize_roll(cmd: str):
    """tokenize_roll.

    Parameters
    ----------
    cmd : str
        Raw command string to tokenize.
    """

    raw = []

    log.info(f'Tokenize: "{cmd}"')
    if isinstance(cmd, str):
        raw = split_tokens(cmd)
    else:
        for arg in cmd:
            raw.extend(split_tokens(arg))

    raw = filter_tokens(raw)

    tokens, tag = [], ''
    for i, token in enumerate(raw):
        if token.startswith('#'):
            tokens = raw[:i]
            tag = ' '.join(raw[i:])
            break
    if not tag:
        tokens = raw
    tag = tag.strip('# ')

    return tokens, tag


def expand_tokens(tokens, mode = None, variables = {}):
    
    if mode is None:
        mode = GameMode.DEFAULT

    if mode is not None and not isinstance(mode, GameMode):
        raise ValueError('mode must be of type GameMode')

    expanded = []

    for token in tokens:
        if token.isnumeric():
            expanded.append(token)
        elif token in OPS:
            expanded.append(token)
        elif token.startswith('$'):
            var = token.strip('$')
            if var in variables:
                val = variables[var]
                if not isinstance(val, int):
                    raise ValueError('Non-integer variable!')
                expanded.append(variables[var])
            else:
                log.error(f'Undefined var: {var}')
                raise ValueError(f'Sorry bruh, that variable isn\'t defined: `{var}`')
        else:
            if token == 'r':
                token = MODE_DICE[mode]

            expanded.append(token)

    return expanded


def parse_tokens(tokens, **kwargs):
    eval_expr = ' '.join((str(token) for token in tokens))
    try:
        return roll_expr(eval_expr, **kwargs), eval_expr
    except DiceBaseException as e:
        raise ValueError(e)


def roll_expression(roll_expr, variables = {}, require_tag=False,
                    game_mode=GameMode.DEFAULT, **kwargs):
    tokens, tag = tokenize_roll(roll_expr)
    expanded = expand_tokens(tokens,
                             mode = game_mode,
                             variables = variables)
    result, eval_expr = parse_tokens(expanded, **kwargs)

    return result, expanded, tag, eval_expr


def extract_rolls(elements, rolls):
    for e in elements:
        if isinstance(e, Dice):
            rolls.append(e)
        elif hasattr(e, 'tokens'):
            extract_rolls(e.tokens, rolls)


class RollHandler:

    def __init__(self, ctx, log, variables, roll,
                       require_tag=False, game_mode=GameMode.DEFAULT):

        log.info(f'Roll request: {roll}')

        self.ctx = ctx
        self.log = log
        self.game_mode = game_mode
        self.roll = roll

        self.tokens, self.tag = tokenize_roll(roll)
        if require_tag and not self.tag:
            raise ValueError('Add a tag, it\'s the polite thing to do.')
        self.log.info(f'Raw tokens: {self.tokens}')

        self.expanded = expand_tokens(self.tokens,
                                      mode = self.game_mode,
                                      variables = variables)
        self.log.info(f'Expanded tokens: {self.expanded}')
        
        result, self.expr = parse_tokens(self.expanded, single=False, raw=True)
        self.result = RollResult(self.expr, result)
        if self.result is None:
            log.error(f'Python parsing error: {eval_expr}.')
            raise ValueError(f'Your syntax was scintillating, but I couldn\'t parse it.')

        log.info(f'Handled roll: {str(self)}')

    async def add_to_db(self, db: ZardozDatabase):
        await db.add_roll(self.ctx.author.id, self.ctx.author.nick, self.ctx.author.name,
                          ' '.join(self.tokens), self.tag, self.expr)

    def msg(self):
        header = f':game_die: {self.ctx.author.mention}' + (f': *{self.tag}*' if self.tag else '')
        result = [f'***Request:***  `{" ".join(self.tokens)}`\n',
                  f'***Rolls:***  `{self.result.describe_rolls()}`\n',
                  f'***Result:***\n```{self.result.describe(mode=self.game_mode)}```']
        result = ''.join(result)
        msg = '\n'.join((header, result))

        return msg

    def __str__(self):
        ret = f'<RollHander'\
              f' cmd="{self.roll}"'\
              f' from={self.ctx.author}'\
              f' guild="{self.ctx.guild}"'\
              f' tokens={self.tokens}'\
              f' tag="{self.tag}"'\
              f' expanded={self.expanded}'\
              f' rolls="{self.result.describe_rolls()}"'\
              f' result={self.result}>'
        return ret


class QuietRollHandler(RollHandler):

    def msg(self):
        header = f'*:game_die: {self.tag}*' if self.tag else ''
        result =f'```{self.result.describe(mode=self.game_mode)}```'
        msg = f'{header}\n{result}'

        return msg


class SekretRollHandler(RollHandler):

    def msg(self):
        header = f':game_die: from **{self.ctx.author}** in **{self.ctx.guild}**: ' + (f'*{self.tag}*' if self.tag else '')
        result = [f'***Request:***  `{" ".join(self.tokens)}`\n',
                  f'***Rolls:***  `{self.result.describe_rolls()}`\n',
                  f'***Result:***\n```{self.result.describe(mode=self.game_mode)}```']
        result = ''.join(result)
        return '\n'.join((header, result))


class RerollHandler(RollHandler):

    def msg(self, reroll_target):
        header = f':game_die: {self.ctx.author.mention} rerolls {reroll_target}' + (f': *{self.tag}*' if self.tag else '')
        result = [f'***Request:***  `{" ".join(self.tokens)}`\n',
                  f'***Rolls:***  `{self.result.describe_rolls()}`\n',
                  f'***Result:***\n```{self.result.describe(mode=self.game_mode)}```']
        result = ''.join(result)
        msg = '\n'.join((header, result))

        return msg


class RollResult:

    def __init__(self, expr, roll):
        self.expr = expr
        self.roll_elements = roll
        try:
            roll = single([e.evaluate_cached(max_dice=MAX_DICE_PER_ROLL) for e in roll])
        except DiceBaseException as e:
            raise ValueError(e)

        if isinstance(roll, int):
            self.roll = [roll]
        else:
            self.roll = []
            for item in roll:
                if isinstance(item, Comparison):
                    self.roll.append(DiceComparison(item))
                else:
                    self.roll.append(DiceResult(item))

    def describe(self, mode='', **kwargs):
        dsc = '\n'.join((r.describe(mode=mode, expr=self.expr) for r in self.roll))
        return dsc if dsc else '0'

    def describe_rolls(self):
        rolls = []
        extract_rolls(self.roll_elements, rolls)
        dsc = []
        for roll in rolls:
            dsc.append(f'{roll} ⤳ {roll.evaluate_cached()}')
        return ', '.join(dsc)

    def __iter__(self):
        for r in self.roll:
            yield r

    def __str__(self):
        roll = self.roll
        if len(self.roll) == 1:
            roll = self.roll[0]
        return f'{{{self.expr} ⤳ {roll}}}'

    def __repr__(self):
        return f'RollList("{self.expr}", {self.roll})'


class DiceResult:

    def __init__(self, result):
        if not isinstance(result, int):
            raise ValueError(f'Must be scalar (got {result}).')
        self.result = result

    def describe(self, **kwargs):
        return f'{self.result}'

    def __int__(self):
        return self.result
    

class DiceComparison(Comparison):

    def __init__(self, other):
        super().__init__(other.left, other.right , other.delta, other.value, other.operator)

    def describe(self, mode = None, expr = '', **kwargs):
        if mode is not None and not isinstance(mode, GameMode):
            raise ValueError('mode must be of type GameMode')
        if mode is GameMode.RT and 'd100' in expr:
            degrees = self.delta // 10
            status = SUCCESS if self.value else FAILURE
            if degrees > 0:
                result = f'{status} {degrees}°'
            else:
                result = status
            return f'{self.left:4} {self.operator} {self.right:<4} ⤳ {result}'
        else:
            kind = f'{SUCCESS} by' if self.value else f'{FAILURE} by'
            return f'{self.left:4} {self.operator} {self.right:<4} ⤳ {kind} {self.delta}'


class SimpleRollConvert(commands.Converter):

    pat = r'^\d+d\d+t?$'

    async def convert(self, ctx, argument):
        match = re.match(self.pat, argument)
        log.info(f'match {argument}')

        if match is None:
            log.info(f'SimpleRollConvert: {argument} did not match')
            raise commands.BadArgument(f'{argument} is not a simple roll.')
        try:
            roll = dice.roll(argument)
        except:
            log.info(f'Failed to parse roll: {argument}')
            raise commands.BadArgument(f'Failed to parse roll: {argument}')
        else:
            log.info(f'SimpleRoll: {argument} ⤳ {roll}')
            return DieResult(argument, int(roll))

