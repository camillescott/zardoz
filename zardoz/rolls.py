#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : rolls.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 22.02.2021

import dice
from dice import DiceBaseException
from discord.ext import commands

import logging
import re

from .database import ZardozDatabase
from .state import GameMode, MODE_DICE
from .utils import SUCCESS, FAILURE


log = logging.getLogger()

OPS = ['+', '-', '<=', '<', '>=', '>', '(', ')', r'#']
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

            ndice = re.match(r'^\d+', token)
            if ndice is not None and int(ndice.group(0)) > 69:
                log.error(f'Too many dice.')
                raise ValueError(f'Woah there cowboy, you trying to crash me? Try using 69 or less dice.')
            try:
                resolved = dice.roll(token)
            except DiceBaseException:
                log.error(f'Got invalid token: {token}.')
                raise ValueError(f'I don\'t like this argument: `{token}`.')
            else:
                log.info(f'Rolled a token: {token} -> {resolved}')
                expanded.append(RollList(token, resolved))

    return expanded


def evaluate_expr(expanded_tokens):
    eval_expr = ' '.join([(repr(t) if not isinstance(t, str) else t) for t in expanded_tokens])
    try:
        return eval(eval_expr), eval_expr
    except SyntaxError as e:
        return None, eval_expr


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
        self.expr =  ' '.join((str(token) for token in self.expanded))
        
        self.result, eval_expr = evaluate_expr(self.expanded)
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
                  f'***Rolled out:***  `{self.expr}`\n',
                  f'***Result:***\n```{self.result.describe(mode=self.game_mode)}```']
        result = ''.join(result)
        msg = '\n'.join((header, result))

        return msg

    def __str__(self):
        ret = f'<RollHander'\
              f' cmd="{self.roll}"'\
              f' from={self.ctx.author}'\
              f' guild={self.ctx.guild}'\
              f' tokens={self.tokens}'\
              f' tag="{self.tag}"'\
              f' expanded={self.expanded}'\
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
                  f'***Rolled out:***  `{self.expr}`\n',
                  f'***Result:***\n```{self.result.describe(mode=self.game_mode)}```']
        result = ''.join(result)
        return '\n'.join((header, result))


class RerollHandler(RollHandler):

    def msg(self, reroll_target):
        header = f':game_die: {self.ctx.author.mention} rerolls {reroll_target}' + (f': *{self.tag}*' if self.tag else '')
        result = [f'***Request:***  `{" ".join(self.tokens)}`\n',
                  f'***Rolled out:***  `{self.expr}`\n',
                  f'***Result:***\n```{self.result.describe(mode=self.game_mode)}```']
        result = ''.join(result)
        msg = '\n'.join((header, result))

        return msg


class DieResult:

    def __init__(self, expr, result):
        if not isinstance(result, int):
            raise ValueError(f'Must be scalar (got {result}).')
        self.expr = expr
        self.result = result

    def __str__(self):
        return f'{self.expr} ⤳ {self.result}'

    def __int__(self):
        return self.result


class RollList:
    def __init__(self, expr, roll):
        self.expr = expr

        if isinstance(roll, int):
            self.roll = [roll]
        else:
            self.roll = list(roll)

    def describe(self, **kwargs):
        dsc = ', '.join((str(r) for r in self.roll))
        return dsc if dsc else '0'

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
    
    def __add__(self, other):
        if isinstance(other, RollList):
            return RollList(f'{self} + {other}', self.roll + other.roll)
        else:
            return RollList(f'{self} + {other}', (r + other for r in self.roll))

    def __neg__(self):
        return RollList(f'-{self}', (-r for r in self.roll))

    def __pos__(self):
        return RollList(f'+{self}', (+r for r in self.roll))

    def __sub__(self, other):
        return RollList(f'{self} - {other}', (r - other for r in self.roll))

    def __lt__(self, other):
        preds =  [r < other for r in self.roll]
        deltas = [abs(other - r) + int(not p) for r, p in zip(self.roll, preds)]
        return DiceDelta(self.roll, deltas, preds, f'{self} < {other}')

    def __le__(self, other):
        preds = [r <= other for r in self.roll]
        deltas = [abs(other - r) for r in self.roll]
        return DiceDelta(self.roll, deltas, preds, f'{self} <= {other}')

    def __eq__(self, other):
        return [r == other for r in self.roll]

    def __gt__(self, other):
        preds = [r > other for r in self.roll]
        deltas = [abs(other - r) + int(not p) for r, p in zip(self.roll, preds)]
        return DiceDelta(self.roll, deltas, preds, f'{self} > {other}')

    def __ge__(self, other):
        preds = [r >= other for r in self.roll]
        deltas = [abs(r - other) for r in self.roll]
        return DiceDelta(self.roll, deltas, preds, f'{self} >= {other}')


class DiceDelta:

    def __init__(self, rolls, deltas, predicates, expr=''):
        self.rolls = rolls
        self.deltas = deltas
        self.predicates = predicates
        self.expr = expr

    def describe(self, mode = None):
        if mode is not None and not isinstance(mode, GameMode):
            raise ValueError('mode must be of type GameMode')
        desc = []
        for roll, delta, pred in zip(self.rolls, self.deltas, self.predicates):
            if mode is GameMode.RT and 'd100' in self.expr:
                degrees = delta // 10
                status = SUCCESS if pred else FAILURE
                if degrees > 0:
                    result = f'{status} {degrees}°'
                else:
                    result = status
                desc.append(f'{roll:4} ⤳ {result}')
            else:
                kind = f'{SUCCESS} by' if pred else f'{FAILURE} by'
                desc.append(f'{roll:4} ⤳ {kind} {delta}')
        desc = '\n'.join(desc)
        return desc if desc else '0'


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

