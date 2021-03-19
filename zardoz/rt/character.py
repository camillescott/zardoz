#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : character.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 25.02.2021

from dataclasses import dataclass
from enum import Enum

from ..utils import require_kwargs


class Characteristic(Enum):
    WeaponSkill = 'WS'
    BallisticSkill = 'BS'
    Strength = 'S'
    Toughness = 'T'
    Agility = 'AG'
    Intelligence = 'INT'
    Perception = 'PER'
    Willpower = 'WP'
    Fellowship = 'FEL'


class CharacteristicInstance:

    def __init__(self, characteristic: Characteristic, base: int):
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
        return (int(self) // 10) * self.multiplier

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
        return f'{self.characteristic.value}={int(self)}: '\
               f'bonus={self.bonus}, advances={self.advances}, '\
               f'modifiers={dict(zip(self.modifier_tags, self.modifiers))}'


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
        self.chars = {
            Characteristic.WeaponSkill.value: CharacteristicInstance(Characteristic.WeaponSkill, base_ws),
            Characteristic.BallisticSkill.value: CharacteristicInstance(Characteristic.BallisticSkill, base_bs),
            Characteristic.Strength.value: CharacteristicInstance(Characteristic.Strength, base_s),
            Characteristic.Toughness.value: CharacteristicInstance(Characteristic.Toughness, base_t),
            Characteristic.Agility.value: CharacteristicInstance(Characteristic.Agility, base_ag),
            Characteristic.Intelligence.value: CharacteristicInstance(Characteristic.Intelligence, base_int),
            Characteristic.Perception.value: CharacteristicInstance(Characteristic.Perception, base_per),
            Characteristic.Willpower.value: CharacteristicInstance(Characteristic.Willpower, base_wp),
            Characteristic.Fellowship.value: CharacteristicInstance(Characteristic.Fellowship, base_fel)
        }
        for name, characteristic in self.chars.items():
            setattr(self, name, characteristic)
        
        self.base_fate = base_fate if base_fate > 0 else 0

    def __str__(self):
        chars = '\n    '.join((str(char) for char in self.chars.values()))
        return f'Player: {self.name}\n'\
                '  Characteristics:\n'\
               f'    {chars}\n'\
               f'  Fate: {self.base_fate}'
