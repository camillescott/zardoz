import dice
from dice import DiceException

import logging
import re

from .state import GameMode, MODE_DICE


log = logging.getLogger('discord')


DELIMS = ['+', '-', '<=', '<', '>=', '>', '(', ')']
SPLIT_PAT = '|'.join(map(re.escape, DELIMS))


def split_operators(word):
    return [t for t in re.split(f'({SPLIT_PAT})', word) if t not in ' ()']


def resolve_expr(roll, *args, mode = None):

    if mode is not None and not isinstance(mode, GameMode):
        raise ValueError('mode must be of type GameMode')

    # first, do split on roll to seperate operators if lacking whitespace
    # we want to handle + and - ourselves rather than leaving it to Dice
    tokens = split_operators(roll)
    for arg in args:
        tokens.extend(split_operators(arg))
   
    sanitized = []

    for token in tokens:
        if token in DELIMS or token.isnumeric():
            sanitized.append(token)
        else:
            if mode is not None and token == 'r':
                token = MODE_DICE[mode]
            try:
                resolved = dice.roll(token)
            except DiceException:
                log.warning(f'Got invalid token: {token}.')
                raise ValueError(f'Invalid expression! Tokens should be rolls, operators, or integers. Got: {token}.')
            else:
                sanitized.append(RollList(token, resolved))

    resolved = ' '.join((str(token) for token in sanitized))

    return sanitized, resolved


def solve_expr(tokens):
    solved = eval(' '.join([(repr(t) if not isinstance(t, str) else t) for t in tokens]))
    return solved


async def handle_roll(ctx, log, db, game_mode, *args):
    log.info(f'Received expr: "{args}" from {ctx.guild}:{ctx.author}')

    roll_expr, tag = [], ''
    for i, token in enumerate(args):
        if token.startswith('#'):
            roll_expr = args[:i]
            tag = ' '.join(args[i:])
    if not tag:
        roll_expr = args
    tag = tag.strip('# ')

    try:
        tokens, resolved = resolve_expr(*roll_expr, mode=game_mode)
        solved = solve_expr(tokens)
    except ValueError  as e:
        log.error(f'Invalid expression: {roll_expr} {e}.')
        await ctx.send(f'You fucked up yer roll, {ctx.author}.')
        return None, None, None, None
    else:
        db.add_roll(ctx.guild, ctx.author, ' '.join(roll_expr), resolved)
        return tag, roll_expr, resolved, solved


class RollList:
    def __init__(self, expr, roll):
        self.expr = expr

        if isinstance(roll, int):
            self.roll = [roll]
        else:
            self.roll = list(roll)

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

    def __sub__(self, other):
        return RollList(f'{self} - {other}', (r - other for r in self.roll))

    def __lt__(self, other):
        deltas = [abs(other - r) for r in self.roll]
        preds =  [r < other for r in self.roll]
        return DiceDelta(self.roll, deltas, preds, f'{self} < {other}')

    def __le__(self, other):
        preds = [r <= other for r in self.roll]
        deltas = [abs(other - r) for r in self.roll]
        return DiceDelta(self.roll, deltas, preds, f'{self} <= {other}')

    def __eq__(self, other):
        return [r == other for r in self.roll]

    def __gt__(self, other):
        preds = [r > other for r in self.roll]
        deltas = [abs(r - other) for r in self.roll]
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
                if degrees > 0:
                    kind = 'DoS' if pred else 'DoF'
                    result = f'{degrees} {kind}'
                else:
                    result = 'success' if pred else 'failure'
                desc.append(f'{roll:4} ⤳ {result}')
            else:
                kind = 'succeeded by' if pred else 'failed by'
                desc.append(f'{roll:4} ⤳ {kind} {delta}')
        return '\n'.join(desc)



