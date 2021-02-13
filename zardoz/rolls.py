import dice
from dice import DiceException

import logging
import re

log = logging.getLogger('discord')


DELIMS = ['+', '-', '<=', '<', '>=', '>', '(', ')']
SPLIT_PAT = '|'.join(map(re.escape, DELIMS))


def split_operators(word):
    return [t for t in re.split(f'({SPLIT_PAT})', word) if t not in ' ()']


def resolve_expr(roll, *args):
    # first, do split on roll to seperate operators if lacking whitespace
    # we want to handle + and - ourselves rather than leaving it to Dice
    tokens = split_operators(roll)
    for arg in args:
        tokens.extend(split_operators(arg))
   
    sanitized = []

    for token in tokens:
        if token in DELIMS:
            sanitized.append(token)
        elif token.isnumeric():
            sanitized.append(token)
        else:
            try:
                resolved = dice.roll(token)
            except DiceException:
                log.warning(f'Got invalid token: {token}.')
                raise ValueError(f'Invalid expression! Tokens should be rolls, operators, or integers. Got: {token}.')
            else:
                sanitized.append(RollList(token, resolved))

    resolved = ' '.join((str(token) for token in sanitized))

    return sanitized, resolved


class RollList:
    def __init__(self, expr, roll):
        self.expr = expr

        if isinstance(roll, int):
            self.roll = [roll]
        else:
            self.roll = list(roll)

    def __str__(self):
        roll = self.roll
        if len(self.roll) == 1:
            roll = self.roll[0]
        return f'{{{self.expr}=>{roll}}}'
    
    def __add__(self, other):
        if isinstance(other, RollList):
            return RollList(self.roll + other.roll)
        else:
            return RollList((r + other for r in other.roll))

    def __lt__(self, other):
        return [r < other for r in self.roll]

    def __le__(self, other):
        return [r <= other for r in self.roll]

    def __eq__(self, other):
        return [r == other for r in self.roll]

    def __gt__(self, other):
        return [r > other for r in self.roll]

    def __ge__(self, other):
        return [r >= other for r in self.roll]
