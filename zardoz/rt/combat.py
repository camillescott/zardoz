#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : combat.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 25.02.2021

from abc import ABC, abstractmethod
import collections
import os

from .character import Characteristic
from ..utils import __pkg_dir__, reverse_number, d10, d100, Nd10
from ..ztable import RollTable


class CharacteristicBonus:

    def __init__(self, characteristic: Characteristic, bonus: int):
        self.characteristic = characteristic
        self.bonus = bonus

    def __int__(self):
        return self.bonus

    def __call__(self, ctx, **kwargs):
        if self.characteristic == ctx.characteristic:
            ctx.add_test_bonus(self.bonus)

    def __str__(self):
        return f'Bonus: {self.characteristic.name} {self.bonus}'


class ExtraHitsBonus:

    def __init__(self, dos_div: int = 1):
        self.dos_div = 1

    def __call__(self, ctx, **kwargs):
        ctx.add_hits(ctx.attack_degrees  // self.dos_div)

    def __str__(self):
        return f'Bonus: 1 hit per {self.dos_div} DoS'


COMBAT_ACTIONS = {}

class CombatAction:

    def __init__(self, name: str, before_effects = None, after_effects = None, special=''):
        self.name = name
        self.before_effects = before_effects if before_effects else []
        self.after_effects = after_effects if after_effects else []
        self.special = special

        COMBAT_ACTIONS[name] = self

    def effects(self):
        if self.before_effects:
            for effect in self.before_effects:
                yield effect
        if self.after_effects:
            for effect in self.after_effects:
                yield effect


AimFull = CombatAction('Aim Full',
                       before_effects = [
                           CharacteristicBonus(Characteristic.WeaponSkill, 20),
                           CharacteristicBonus(Characteristic.BallisticSkill, 20)
                       ])

AimHalf = CombatAction('Aim Half',
                       before_effects = [
                           CharacteristicBonus(Characteristic.WeaponSkill, 10),
                           CharacteristicBonus(Characteristic.BallisticSkill, 10)
                       ])

AllOutAttack = CombatAction('All Out Attack',
                            before_effects = [
                                CharacteristicBonus(Characteristic.WeaponSkill, 20)
                            ],
                            special='Cannot dodge or parry')

CalledShot = CombatAction('Called Shot',
                          before_effects = [
                              CharacteristicBonus(Characteristic.WeaponSkill, 20),
                              CharacteristicBonus(Characteristic.BallisticSkill, 20)
                          ],
                          special='Attack a specific location')

Charge = CombatAction('Charge',
                      before_effects = [
                          CharacteristicBonus(Characteristic.WeaponSkill, 10)
                      ],
                      special='Must move 4 metres')

FullAutoBurst = CombatAction('Full Auto Burst',
                             before_effects  = [
                                 CharacteristicBonus(Characteristic.BallisticSkill, 20)
                             ],
                             after_effects = [
                                 ExtraHitsBonus()
                             ])

SemiAutoBurst = CombatAction('Semi Auto Burst',
                             before_effects = [
                                 CharacteristicBonus(Characteristic.BallisticSkill, 10)
                             ],
                             after_effects = [
                                 ExtraHitsBonus(dos_div=2)
                             ])


class HitLocTable:

    def __init__(self):

        self.base = RollTable(os.path.join(__pkg_dir__, 'tables', 'rt_hit_loc.yaml'))
        self.table = {'Head': ['Head', 'Arm', 'Body', 'Arm', 'Body'],
                      'Arm':  ['Arm', 'Body', 'Head', 'Body', 'Arm'],
                      'Body': ['Body', 'Arm', 'Head', 'Arm', 'Body'],
                      'Leg':  ['Leg', 'Body', 'Arm', 'Head', 'Body']}

    def get_location(self, init_roll, n_hits):
        table_val = reverse_number(init_roll)
        locs = []
        _, init_loc = self.base.get(table_val)
        locs.append(init_loc)

        if n_hits > 1:
            x_hits = n_hits - 1
            idx_loc = init_loc
            if 'Arm' in idx_loc:
                idx_loc = 'Arm'
            if 'Leg' in idx_loc:
                idx_loc = 'Leg'

            subtable = self.table[idx_loc]
            locs.extend(subtable[:x_hits])
            if x_hits > len(subtable):
                locs.extend([subtable[-1]] * (x_hits - len(subtable)))

        return locs
    
HIT_LOC_TABLE = HitLocTable()


class DamageRoll:

    def __init__(self, dice, bonus):
        self.bonus = bonus
        self.fury_bonus = 0
        self.dice = dice

    def replace_lowest(self, replacement):
        if min(self.dice) < replacement:
            self.dice[self.dice.index(min(self.dice))] = replacement

    def __int__(self):
        return sum(self.dice) + self.bonus + self.fury_bonus

    def add_fury(self, extra_fury):
        self.fury_bonus += extra_fury

    def add_bonus(self, extra_bonus):
        self.bonus += extra_bonus


class AttackContext:

    def __init__(self, weapon, test_base, target_range, actions = [], quiet: bool = True):
        self.characteristic = weapon.test_characteristic
        self.test_base = test_base
        self.weapon = weapon
        self._test_bonus = 0
        self.target_range = target_range
        self.hits_base = 0
        self.hits_extra = 0
        self.actions = actions

        self.attack_roll = 0
        self.attack_degrees = 0

        self.damage = 0
        self.damage_bonus = 0
        self.damage_rolls = []

    def add_test_bonus(self, extra):
        self._test_bonus += extra

    def add_hits(self, extra):
        self.hits_extra += extra

    def add_damage_roll(self, roll):
        self.damage_rolls.append(roll)

    @property
    def test_bonus(self):
        return min(60, self._test_bonus)

    @property
    def test(self):
        return self.test_base + self.test_bonus

    @property
    def hits(self):
        if SemiAutoBurst in self.actions:
            hits_max = self.weapon.rof_semi
        elif FullAutoBurst in self.actions:
            hits_max = self.weapon.rof_auto
        else:
            hits_max = int(self.weapon.rof_single)
        return min(self.hits_base + self.hits_extra, hits_max)

    @property
    def success(self):
        return self.attack_roll <= self.test

    @property
    def total_damage(self):
        return sum((int(roll) for roll in self.damage_rolls))


def player_attack(weapon_instance, char_val, actions=None, target_range: int = 10, quiet: bool = True):

        def _print(*args, **kwargs):
            if not quiet:
                print(*args, **kwargs)

        #
        # Sanitize parameters
        #

        if actions is None:
            actions = []
        elif not isinstance(actions, collections.Sequence):
            actions = set([actions])
        else:
            actions = set(actions)

        assert len(actions) < 3

        if SemiAutoBurst in actions and not weapon_instance.rof_semi:
            raise ValueError(f'{weapon_instance.name} does not support semi-auto')
        if FullAutoBurst in actions and not weapon_instance.rof_auto:
            raise ValueError(f'{weapon_instance.name} does not support full-auto')
        if target_range / weapon_instance.range > 4:
            raise ValueError(f'{weapon_instance.name} cannot fire more than {weapon_instance.range * 4}m')

        # setup the attack context
        ctx = AttackContext(weapon_instance, char_val, target_range, actions=actions, quiet=quiet)

        # apply characteristic bonuses
        for action in actions:
            for bonus in action.before_effects:
                bonus(ctx)
                _print(bonus)
        # now we'd apply specials from the weapon itself in the same way

        # figure ranges
        if target_range <= 2:
            # point blank
            _print('Point blank: +30')
            ctx.add_test_bonus(30)
        elif target_range <= (weapon_instance.range / 2):
            # short range
            ctx.add_test_bonus(10)
            _print('Close: +10')
        elif target_range >= (weapon_instance.range * 3):
            # extreme range
            ctx.add_test_bonus(-30)
            _print('Extreme: -30')
        elif target_range >= (weapon_instance.range * 2):
            # long range
            ctx.add_test_bonus(-10)
            _print('Long: -10')
        else:
            _print('Normal range.')

        _print(f'final test: {ctx.test_base} + {ctx.test_bonus}')

        # roll it
        ctx.attack_roll = d100()
        delta = abs(ctx.test - ctx.attack_roll)
        ctx.attack_degrees = delta // 10

        _print(f'rolled {ctx.attack_roll} for {ctx.attack_degrees} degrees')

        # TODO: check jamming and exploding

        if not ctx.success:
            # damage, effective_char, degrees, hits, locations, message
            return 0, ctx.test, ctx.attack_degrees, 0, [], "Failed to hit"
        else:
            ctx.hits_base = 1

        # apply action bonuses
        for action in actions:
            for bonus in action.after_effects:
                bonus(ctx)
                _print(bonus)

        _print(f'hits after bonus: {ctx.hits}')

        # get hit location with reverse_number
        # for multiple hits 

        # roll for damage
        for hit_counter in range(ctx.hits):
            _print(f'roll hit {hit_counter + 1}')

            roll = DamageRoll(Nd10(n=weapon_instance.damage_roll), weapon_instance.damage_bonus)

            _print(f'initial damage roll: {roll.dice}')

            # replace lowest with DoS if its lower
            roll.replace_lowest(ctx.attack_degrees)

            _print(f'damage roll after replace: {roll.dice}')

            # TODO: apply weapon special roll bonuses

            ctx.add_damage_roll(roll)
            _print(f'damage before fury: {int(roll)}')

            fury = 10 in roll.dice
            while (fury):
                fury_roll = d100() <= ctx.test

                if fury_roll:
                    fury_damage = d10()

                    _print(f'fury! rolled {fury_damage}')

                    roll.add_fury(fury_damage)
                    fury = fury_damage == 10
                else:
                    fury = False

        _print(f'final damage: {ctx.total_damage}')
                

        locs = HIT_LOC_TABLE.get_location(ctx.attack_roll, ctx.hits)
        return ctx.total_damage, ctx.test, ctx.attack_degrees, ctx.hits, locs, "Hit!"
