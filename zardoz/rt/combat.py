#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : combat.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 25.02.2021

from abc import ABC, abstractmethod

from .character import Characteristic


class CharacteristicBonus:

    def __init__(self, characteristic: Characteristic, bonus: int):
        self.characteristic = characteristic
        self.bonus = bonus

    def __int__(self):
        return self.bonus

    def __call__(self, ctx, **kwargs):
        ctx.test_bonus += bonus


class ExtraHitsBonus:

    def __init__(self, dos_div: int = 1):
        self.dos_div = 1

    def __call__(self, ctx, *, dos: int, **kwargs):
        return dos // self.dos_div


class CombatAction:

    def __init__(self, name: str, before_effects = None, after_effects = None, special=''):
        self.name = name
        self.before_effects = before_effects if before_effects else []
        self.after_effects = after_effects if after_effects else []
        self.special = special

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
