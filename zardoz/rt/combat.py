#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : combat.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 25.02.2021

from abc import ABC, abstractmethod
import os

from .character import Characteristic
from ..utils import __pkg_dir__, reverse_number
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
