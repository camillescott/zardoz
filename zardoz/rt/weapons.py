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

from ..utils import require_kwargs, reverse_number
from .character import Characteristic
from .combat import (CombatAction, CharacteristicBonus, ExtraHitsBonus,
                     FullAutoBurst, SemiAutoBurst)


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
    availability: ItemAvailability

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
    special: tuple = field(default_factory=tuple)
    extra: str = ''
    reference: str = ''


class InstanceMixin:

    def __init__(self, *,
                 craftsmanship: Craftsmanship,
                 quantity: int = 1,
                 **kwargs):
        print(kwargs)
        self.craftsmanship = craftsmanship
        self.quantity = quantity
        
        super().__init__(**kwargs)


class WeaponInstance(InstanceMixin):

    def __init__(self, weapon_model: Weapon, *,
                 craftsmanship: Craftsmanship,
                 quantity: int = 1):

        self.weapon_model = weapon_model
        self.test_characteristic = Characteristic.WeaponSkill \
            if self.weapon_model.weapon_class == WeaponClass.Melee \
            else Characteristic.BallisticSkill
        
        super().__init__(craftsmanship=craftsmanship,
                         quantity=quantity)

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

    def _attack(self, char_val, action, target_range: int = 10):
        single, semi, auto = self.weapon_model.rof

        if action is SemiAutoBurst and not semi:
            raise ValueError(f'{self.name} does not support semi-auto')
        if action is FullAutoBurst and not auto:
            raise ValueError(f'{self.name} does not support full-auto')
        if target_range / self.range > 4:
            raise ValueError(f'{self.name} cannot fire more than {self.range * 4}m')

        test = char_val


        # apply characteristic bonuses
        for bonus in action.before_effects:
            if isinstance(bonus, CharacteristicBonus) and bonus.characteristic == self.test_characteristic:
                test += int(bonus)
                print(f'add {bonus} for {test}')
        # now we'd apply specials from the weapon itself in the same way

        # figure ranges
        if target_range <= 2:
            # point blank
            test += 30
        elif target_range < (self.range / 2):
            # short range
            test += 10
        elif target_range > (self.range * 3):
            # extreme range
            test -= 30
        elif target_range > (self.range * 2):
            # long range
            test -= 10
        print(f'added range bonus for {test}')
        test = min(test, 60)
        print(f'final bonus: {test}')

        # roll it
        roll = int(dice.roll('1d100'))
        delta = abs(test - roll)
        degrees = delta // 10
        print(f'rolled {roll} for {degrees} degrees')

        if roll > test:
            # failure
            # damage, degrees, hits, locations, message
            return 0, degrees, 0, [], "Failed to hit"

        hits = 1

        # apply action bonuses
        for bonus in action.after_effects:
            if isinstance(bonus, ExtraHitsBonus):
                # TODO: check for semi or full and use min
                hits += bonus(dos=degrees)

        print(f'hits after bonus: {hits}')

        # get hit location with reverse_number
        # for multiple hits 

        # roll for damage
        damage = 0

        _hits = hits
        while _hits > 0:
            print(f'roll hit {_hits}')
            rolls = list(dice.roll(self.damage_roll))
            print(f'damage rolls: {rolls}')
            # replace lowest with DoS if its lower
            if min(rolls) < degrees:
                rolls[rolls.index(min(rolls))] = degrees
            print(f'damage rolls after replace: {rolls}')
            damage += sum(rolls) + self.damage_bonus
            print(f'damage before fury: {damage}')

            fury = 10 in rolls
            while (fury):
                fury_roll = int(dice.roll('1d100')) <= test
                print(f'fury! rolled {fury_roll}')
                if fury_roll:
                    fury_damage = int(dice.roll('1d10'))
                    print(f'fury did {fury_damage}')
                    damage += fury_damage
                    fury = fury_damage == 10
                else:
                    fury = False

            _hits -= 1

        print(f'final damage: {damage}')
                

        return damage, degrees, hits, [], "Hit!"
