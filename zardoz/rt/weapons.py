#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Camille Scott, 2021
# File   : weapons.py
# License: MIT
# Author : Camille Scott <camille.scott.w@gmail.com>
# Date   : 23.02.2021

from dataclasses import dataclass, field
from enum import IntEnum, auto

import dice

from .utils import require_kwargs


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


class Craftsmanship(IntEnum):
    Poor = 10
    Common = 0
    Good = -10
    Best = -30


class ItemAvailability(IntEnum):
    Ubiquitous = 70
    Abundant = 50
    Plentiful = 30
    Common = 20
    Average = 10
    Scarce = 0
    Rare = -10
    VeryRare = -20
    ExtremelyRare = -30
    NearUnique = -50
    Unique = -70


class ItemScale(IntEnum):
    Negligible = 30
    Trivial = 20
    Minor = 10
    Standard = 0
    Major = - 10
    Signficant = -20
    Vast = -30

    @staticmethod
    def from_quantity(q):
        if q == 1:
            return ItemScale.Negligible
        elif 2 <= q < 9:
            return ItemScale.Trivial
        elif 10 <= q < 30:
            return ItemScale.Minor
        elif 30 <= q < 500:
            return ItemScale.Standard
        elif 500 <= q < 2000:
            return ItemScale.Major
        elif 2000 <= q < 10000:
            return ItemScale.Signficant
        else:
            return ItemScale.Vast


@require_kwargs
@dataclass(frozen=True)
class Item:

    name: str
    availability: ItemAvailability = ItemAvailability.Scarce

    def roll_acquisition(self,
                         quantity: int,
                         profit_factor: int,
                         craftsmanship: Craftsmanship = Craftsmanship.Common,
                         modifier: int = 0):

        roll = dice.roll('1d100')
        return int(roll) <= profit_factor + quantity + self.availability + craftsmanship + modifier


@require_kwargs
@dataclass(frozen=True)
class Weapon(Item):

    weapon_class: WeaponClass
    weapon_type: WeaponType
    weapon_range: int
    rof: tuple
    damage_roll: str
    damage_bonus: int
    damage_type: DamageType
    pen: int
    clip: int
    reload_time: float
    mass: float
    avail: ItemAvailability
    craft: Craftsmanship
    special: tuple = field(default_factory=tuple)
    extra: str = ''
    reference: str = ''


class InstanceMixin:

    def __init__(self, *
                 craftsmanship: Craftsmanship,
                 quantity: int = 1):
        self.craftsmanship = craftsmanship
        self.quantity = quantity

