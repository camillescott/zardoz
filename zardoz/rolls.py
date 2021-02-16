import dice
from dice import DiceException
from discord.ext import commands

import logging
import re

from .state import GameMode, MODE_DICE


log = logging.getLogger()


DELIMS = ['+', '-', '<=', '<', '>=', '>', '(', ')', '#', '\s']
SPLIT_PAT = '|'.join(map(re.escape, DELIMS))


def split_operators(word):
    return [t for t in re.split(f'({SPLIT_PAT})', word) if t not in ' ()']


def tokenize_roll(cmd):

    raw = []

    if isinstance(cmd, str):
        raw = split_operators(cmd)
    else:
        for arg in cmd:
            raw.extend(split_operators(arg))

    raw = [token.strip() for token in raw]

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
        elif token in DELIMS:
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
            except DiceException:
                log.error(f'Got invalid token: {token}.')
                raise ValueError(f'I don\'t like this argument: `{token}`.')
            else:
                expanded.append(RollList(token, resolved))

    return expanded


def evaluate_expr(expanded_tokens):
    eval_expr = ' '.join([(repr(t) if not isinstance(t, str) else t) for t in expanded_tokens])
    try:
        return eval(eval_expr), eval_expr
    except SyntaxError as e:
        return None, eval_expr


class RollHandler:

    def __init__(self, ctx, log, db, roll, require_tag=False):

        log.info(f'Roll request: {roll}')

        self.ctx = ctx
        self.log = log
        self.db = db
        self.game_mode = db.get_guild_mode(ctx.guild)

        variables = db.get_guild_vars(ctx.guild)
        self.roll = roll
        self.tokens, self.tag = tokenize_roll(roll)
        if require_tag and not self.tag:
            raise ValueError('Add a tag, it\'s the polite thing to do.')

        self.expanded = expand_tokens(self.tokens,
                                      mode = self.game_mode,
                                      variables = variables)
        self.expr =  ' '.join((str(token) for token in self.expanded))

        
        self.result, eval_expr = evaluate_expr(self.expanded)
        if self.result is None:
            log.error(f'Python parsing error: {eval_expr}.')
            raise ValueError(f'Your syntax was scintillating, but I couldn\'t parse it.')

        db.add_roll(ctx.guild, ctx.author, ' '.join(self.tokens), self.expr)
        log.info(f'Handled roll: {str(self)}')

    def msg(self):
        header = f':game_die: {self.ctx.author.mention}' + (f': *{self.tag}*' if self.tag else '')
        result = [f'*Request:*\n```{" ".join(self.tokens)}```',
                  f'*Rolled out:*\n```{self.expr}```',
                  f'*Result:*\n```{self.result.describe(mode=self.game_mode)}```']
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
        header = f'from **{self.ctx.author}** in **{self.ctx.guild}**: ' + (f'*{self.tag}*' if self.tag else '')
        result = [f'*Request:*\n```{" ".join(self.tokens)}```',
                  f'*Rolled out:*\n```{self.expr}```',
                  f'*Result:*\n```{self.result.describe(mode=self.game_mode)}```']
        result = ''.join(result)
        return '\n'.join((header, result))


class RollList:
    def __init__(self, expr, roll):
        self.expr = expr

        if isinstance(roll, int):
            self.roll = [roll]
        else:
            self.roll = list(roll)

    def describe(self, **kwargs):
        return ', '.join((str(r) for r in self.roll))

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
                if degrees > 0:
                    kind = 'DoS' if pred else 'DoF'
                    result = f'{degrees} {kind}'
                else:
                    result = 'success' if pred else 'failure'
                desc.append(f'{roll:4} ⤳ {result}')
            else:
                kind = 'S by' if pred else 'F by'
                desc.append(f'{roll:4} ⤳ {kind} {delta}')
        return '\n'.join(desc)


class SimpleRollConvert(commands.Converter):

    pat = r'^\d+d\d+t?$'

    async def convert(self, ctx, argument):
        match = re.match(pat, argument)
        if match is None:
            raise commands.BadArgument(f'{argument} is not a simple roll.')
        try:
            roll = dice.roll(argument)
        except:
            raise commands.BadArgument(f'Failed to parse roll: {argument}')
        else:
            log.info(f'SimpleRoll: {argument} ⤳ {roll}')
            if isinstance(roll, int):
                return roll
            else:
                return sum(roll)

