#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : character.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 25.02.2021

from dataclasses import dataclass
from enum import IntEnum, auto

from ..utils import require_kwargs


class Characteristic(IntEnum):
    WeaponSkill = auto()
    BallisticSkill = auto()
    Strength = auto()
    Toughness = auto()
    Agility = auto()
    Intelligence = auto()
    Perception = auto()
    Willpower = auto()
    Fellowship = auto()


class CharacteristicInstance:

    def __init__(self, *, characteristic: Characteristic, base: int):
        self.characteristic = characteristic
        self.base = base
        self.modifiers = []
        self.modifier_tags = []
        self.advances = 0
        self.multiplier = 1

    def __int__(self):
        return self.base + (self.advances * 5) + sum(self.modifiers)

    @property
    def bonus(self):
        return (self.base // 10) * self.multiplier

    def advance(self):
        if self.advances < 4:
            self.advances += 1

    def add_modifier(self, modifier: int, tag: str = ''):
        self.modifiers.append(modifier)
        self.modifier_tags.append(tag)

    def clear_modifiers(self):
        self.modifiers = []
        self.modifier_tags = []

    def __str__(self):
        return f'({self.characteristic.name}={int(self)}, '\
               f'bonus={self.bonus}, advances={self.advances}, '\
               f'modifiers={dict(zip(self.modifier_tags, self.modifiers))})'


class Player:

    def __init__(self, *,
                 name: str,
                 base_ws: int,
                 base_bs: int,
                 base_s: int,
                 base_t: int,
                 base_ag: int,
                 base_int: int,
                 base_per: int,
                 base_wp: int,
                 base_fel: int,
                 base_fate: int):

        if name == '':
            raise ValueError('Player must have a name!')

        self.name = name

        self.WS = CharacteristicInstance(Characteristic.WeaponSkill, base_ws)
        self.BS = CharacteristicInstance(Characteristic.BallisticSkill, base_bs)
        self.S = CharacteristicInstance(Characteristic.Strength, base_s)
        self.T = CharacteristicInstance(Characteristic.Toughness, base_t)
        self.AG = CharacteristicInstance(Characteristic.Agility, base_ag)
        self.INT = CharacteristicInstance(Characteristic.Intelligence, base_int)
        self.PER = CharacteristicInstance(Characteristic.Perception, base_per)
        self.WP = CharacteristicInstance(Characteristic.Willpower, base_wp)
        self.FEL = CharacteristicInstance(Characteristic.Fellowship, base_fel)
        
        self.base_fate = base_fate if base_fate > 0 else 0


