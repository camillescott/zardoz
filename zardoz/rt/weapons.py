#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : weapons.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 23.02.2021

import collections
from dataclasses import dataclass, field
from enum import IntEnum, auto

import dice

from ..utils import require_kwargs, reverse_number, d10, d100, Nd10
from .character import Characteristic
from .items import Craftsmanship, InstanceMixin, Item


class WeaponClass(IntEnum):
    Pistol = auto()
    Basic = auto()
    Heavy = auto()
    Thrown = auto()
    Melee = auto()


class DamageType(IntEnum):
    Energy = auto()
    Impact = auto()
    Rending = auto()
    Explosive = auto()


class WeaponType(IntEnum):
    Las = auto()
    SP = auto()
    Bolt = auto()
    Melta = auto()
    Plasma = auto()
    Flame = auto()
    Primitive = auto()
    Launcher = auto()
    Grenade = auto()
    Missile = auto()
    Exotic = auto()
    Xenos = auto()
    Chain = auto()
    Shock = auto()
    Power = auto()
    Force = auto()
    Ork = auto()


class ShotType(IntEnum):
    Single = auto()
    Semi = auto()
    Full = auto()


@require_kwargs
@dataclass(frozen=True)
class PlayerWeapon(Item):

    weapon_class: WeaponClass
    weapon_type: WeaponType
    weapon_range: int
    rof: tuple
    damage_roll: int
    damage_bonus: int
    damage_type: DamageType
    pen: int
    clip: int
    reload_time: float
    special: tuple = field(default_factory=tuple)
    reference: str = ''
    extra: str = ''

    @property
    def pretty_rof(self):
        single = 'S' if self.rof[0] else '-'
        semi = str(self.rof[1]) if self.rof[1] else '-'
        auto = str(self.rof[2]) if self.rof[2] else '-'
        return f'{single}/{semi}/{auto}'

    @property
    def pretty_damage_type(self):
        return self.damage_type.name[0]


@require_kwargs
@dataclass(frozen=True)
class PlayerWeaponUpgrade(Item):
    pass


class PlayerWeaponInstance(InstanceMixin):

    def __init__(self, weapon_model: PlayerWeapon, *,
                       craftsmanship: Craftsmanship,
                       upgrades = None,
                       quantity: int = 1):

        self.weapon_model = weapon_model
        self.test_characteristic = Characteristic.WeaponSkill \
            if self.weapon_model.weapon_class == WeaponClass.Melee \
            else Characteristic.BallisticSkill

        self.upgrades = [] if upgrades is None else upgrades
        
        super().__init__(craftsmanship=craftsmanship,
                         quantity=quantity)

    def __str__(self):
        return f'<{self.name} {self.damage_roll}d10+{self.damage_bonus}{self.pretty_damage_type} {self.pretty_rof} {self.range}m>'

    @property
    def range(self):
        return self.weapon_model.weapon_range

    @property
    def name(self):
        return self.weapon_model.name

    @property
    def damage_bonus(self):
        return self.weapon_model.damage_bonus

    @property
    def damage_roll(self):
        return self.weapon_model.damage_roll

    @property
    def rof_single(self):
        return self.weapon_model.rof[0]

    @property
    def rof_semi(self):
        return self.weapon_model.rof[1]

    @property
    def pretty_rof(self):
        return self.weapon_model.pretty_rof

    @property
    def pretty_damage_type(self):
        return self.weapon_model.pretty_damage_type

    @property
    def rof_auto(self):
        return self.weapon_model.rof[2]

